from __future__ import print_function
import os
import sys
import argparse
import gettext
from OpenSSL import crypto
from socket import gethostname
from sscg import DEFAULT_CA_CERT, DEFAULT_KEY_STRENGTH, DEFAULT_LIFESPAN, \
                 DEFAULT_CERT_FORMAT, DEFAULT_HASH_ALG, write_certificate,\
    write_certificate_key
from sscg.authority import create_temp_ca
from sscg.service import create_service_cert

# Translation header
PACKAGE = 'sscg'
LOCALEDIR = '/usr/share/locale'
translation = gettext.translation(PACKAGE, LOCALEDIR, fallback=True)
_ = translation.gettext

def parse_cmdline():
    parser = argparse.ArgumentParser(description="Generate a self-signed service certificate")

    parser.add_argument("--debug",
                             help=_("Enable logging of debug messages."),
                             action="store_true")

    # ==== Output Arguments ====
    output_args = parser.add_argument_group('Output')
    
    output_args.add_argument("--cert-format",
                             help=_("Certificate file format. Default=PEM"),
                             choices=("PEM", "ASN1"),
                             default=DEFAULT_CERT_FORMAT)

    output_args.add_argument("--lifetime",
                             help=_("Certificate lifetime (days). Default=3650 (10 years)"),
                             default=DEFAULT_LIFESPAN)

    output_args.add_argument("--key-strength",
                             help=_("Strength of the certificate private keys in bits. Default=2048"),
                             choices=(512, 1024, 2048, 4096),
                             default=DEFAULT_KEY_STRENGTH)

    output_args.add_argument("--hash-alg",
                             help=_("Hashing algorithm to use for signing. Default=sha256"),
                             choices=("md4",
                                      "md5",
                                      "ripemd160",
                                      "sha",
                                      "sha1",
                                      "sha224",
                                      "sha256",
                                      "sha384",
                                      "sha512",
                                      "whirlpool"),
                             default=DEFAULT_HASH_ALG)

    # Package name
    output_args.add_argument("--package",
                             help=_("The name of the package needing a certificate"),
                             required=True)

    # Output files
    output_args.add_argument("--ca-file",
                             help=_("Path where the public CA certificate will be stored. Default: {}".format(
                                    DEFAULT_CA_CERT)),
                             default=DEFAULT_CA_CERT)

    output_args.add_argument("--cert-file",
                             help=_("Path where the public service certificate will be stored."),
                             required=True)
    
    output_args.add_argument("--cert-key-file",
                             help=_("Path where the private key of the service certificate will be stored"),
                             required=True)

    # Subject
    cert_args = parser.add_argument_group('Certificate Details')
    cert_args.add_argument("--hostname",
                        help=_("The valid hostname of the certificate. Must be an FQDN. Default: system hostname"),
                        default=gethostname())

    cert_args.add_argument("--subject-alt-names",
                           help=_("One or more additional valid hostnames for the certificate"),
                           nargs="+")

    # SSL Organization Configuration
    cert_args.add_argument("--country",
                       help=_("Certificate DN: Country (C)"),
                       required=True)

    cert_args.add_argument("--state",
                       help=_("Certificate DN: State (ST)"),
                       required=True)

    cert_args.add_argument("--locality",
                       help=_("Certificate DN: Locality (L)"),
                       required=True)

    cert_args.add_argument("--organization",
                        help=_("Certificate DN: Organization (O)"),
                        required=True)

    cert_args.add_argument("--organizational-unit",
                        help=_("Certificate DN: Organizational Unit (OU)"),
                        required=True)

    options = parser.parse_args()
    if options.cert_format == "PEM":
        options.cert_format = crypto.FILETYPE_PEM
    elif options.cert_format == "ASN1":
        options.cert_format = crypto.FILETYPE_ASN1
    else:
        print (_("Certificate file must be PEM or ASN.1"),
               file=sys.stderr)

    if options.debug:
        # Dump all of the options so we see their values, including defaults
        print (_("Options: {}".format(repr(options))))

    return options


def main():
    options = parse_cmdline()

    (ca_cert, ca_key) = create_temp_ca(options)
    if options.debug:
        print (_("CA Certificate - Public Key"))
        print (crypto.dump_certificate(options.cert_format, ca_cert).decode("UTF-8"))

    (svc_cert, svc_key) = create_service_cert(options, ca_cert, ca_key)
    if options.debug:
        print (_("Service Certificate - Public Key"))
        print (crypto.dump_certificate(options.cert_format, svc_cert).decode("UTF-8"))
        print (_("Service Certificate - Private Key"))
        print (crypto.dump_privatekey(options.cert_format, svc_key).decode("UTF-8"))

    try:
        # Write out the CA Certificate
        write_certificate(options, ca_cert, options.ca_file)
        
        # Write out the Service Certificate
        write_certificate(options, svc_cert, options.cert_file)
    
        # Write out the Service Private Key
        write_certificate_key(options, svc_key, options.cert_key_file)
    except:
        print (_("Error writing certificate files: {}".format(sys.exc_info()[1])),
               file=sys.stderr)

        for file in [options.ca_file, options.cert_file, options.cert_key_file]:
            try:
                os.unlink(file)
            except:
                # Nothing we can do if we get an error
                pass
    


if __name__ == "__main__":
    main()