#!/usr/bin/env python3

import argparse
import hashlib
import logging
import os
from OpenSSL import crypto

LOG = logging.getLogger(__name__)
TYPE_RSA = crypto.TYPE_RSA
TYPE_DSA = crypto.TYPE_DSA
SUBJECT = {
    'C': 'US',
    'ST': 'New York',
    'L': 'New York',
    'O': 'Evil Corp',
    'OU': 'DevOps Automation'
}


class CertificateGenerator:

    def create_local_path(self, path):
        """
        Create local path for backups

        :param path: Local path to create
        """

        LOG.info('Creating path {0}'.format(path))
        if not os.path.exists(path):
            os.makedirs(path)

    def create_timestamp(self, years=1):
        """
        Return a time stamp in seconds encompassing a certain number of years
        Ex:
        Using the default of one year, we get the value 31536000
        60 * 60 * 24 *365 *1
        31536000

        :param years (int):
        :return integer (int): timestamp in seconds
        """

        return 60 * 60 * 24 * 365 * years

    def generate_csr(self, pkey, digest='sha256', **name):
        """
        Given private key pkey, digest and a common name kwargs create a
        certificate signing request

        :param pkey: Private key to use
        :param digest (str): Digest method to use for signing,
                             default is sha256
        :param name (dict): Dictionary of certificate subject data to use
        :return (X509Req Object): Certificate request object
        """

        req = crypto.X509Req()
        subj = req.get_subject()

        for key, value in name.items():
            LOG.debug('key {0} value {1}'.format(key, value))
            setattr(subj, key, value)

        req.set_pubkey(pkey)
        req.sign(pkey, digest)

        return req

    def generate_certificate(self, req, issuer_cert, issuer_key, serial,
                             not_before, not_after, digest="sha256"):
        """
        Generate a certificate given a certificate request.

        :param req (x509Req object): Certificate reqeust to use
        :param issuer_cert (x509 object): The certificate of the issuer
        :param issuer_key (PKey object): The private key of the issuer
        :param serial (int): Serial number for the certificate
        :param not_before (int): Timestamp in seconds (relative to now) when
                                 the certificate starts being valid.
        :param not_after (int): Timestamp in seconds(relative to now) when the
                                certificate stops being valid.
        :param digest (str): Digest method to use for signing,
                             default is sha256
        :return (X509 object) : The signed certificate in an X509 object
        """

        cert = crypto.X509()
        LOG.debug('Serial is {0}'.format(serial))
        cert.set_serial_number(serial)
        cert.gmtime_adj_notBefore(not_before)
        cert.gmtime_adj_notAfter(not_after)
        cert.set_issuer(issuer_cert.get_subject())
        cert.set_subject(req.get_subject())
        cert.set_pubkey(req.get_pubkey())
        cert.sign(issuer_key, digest)

        return cert

    def generate_keypair(self, algo_type, bits):
        """
        Given a type of TYPE_RSA or TYPE_DSA and an integer of bits, generate a
        private key.

        :param type (str): The type of encryption algorithm to use
        :param bits (int):
        :return (crypto.Pkey object): Private key
        """

        pkey = crypto.PKey()
        pkey.generate_key(algo_type, bits)

        return pkey

    def generate_serial(self, cname='localhost.localdomain'):
        """

        :param cname: Common name or hostname
        :return: An integer of hexdigest in base 16
        """

        serial_hash = hashlib.sha256()
        serial_hash.update(cname.encode())

        return int(serial_hash.hexdigest(), 16)

    def generate_cert_data(self, cname, bits=4096, years=5, **ca_data):
        """
        Creates a certificate bundle, which is returned in a dictionary
        for the write certs method.

        :param bits (int): Number of bits to use in the private keys
        :param ca_data (dict): dictionary of ca req and keys
        :param years (int): Number of years the certs are valid
        :return cert_data (dict): Dictionary of key and filename data
        """

        cert_data = {}
        key = self.generate_keypair(TYPE_RSA, bits)
        subject = SUBJECT
        subject['CN'] = cname
        req = self.generate_csr(key, **subject)
        not_after = self.create_timestamp(years)
        if ca_data:
            cert_data['fname'] = cname.replace('.', '-')
            cakey = ca_data['key']
            careq = ca_data['req']
            serial = self.generate_serial(cname)
        else:
            # We're self-signing because this is the ca
            cert_data['fname'] = '{0}-CA'.format(cname.replace('.', '-'))
            cakey = key
            careq = req
            serial = 0
        cert = self.generate_certificate(req, careq, cakey, serial, 0,
                                         not_after)
        cert_data['req'] = req
        cert_data['key'] = key
        cert_data['cert'] = cert

        return cert_data

    def write_certs(self, path, **cert_data):
        """
        Write certificate bundle to file

        :param path (os.path object): The path to store the certs in
        :param cert_data (dict): Dictionary of cert, request, private key and
                                 filename data.
        """

        req_pem = crypto.dump_certificate_request(crypto.FILETYPE_PEM,
                                                  cert_data['req'])
        pkey_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                          cert_data['key'])
        cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM,
                                           cert_data['cert'])
        fname = cert_data['fname']
        with open('{0}/{1}.csr'.format(path, fname), 'w') as fname_file:
            fname_file.write(req_pem.decode('utf-8'))

        with open('{0}/{1}.pkey'.format(path, fname), 'w') as fname_file:
            fname_file.write(pkey_pem.decode('utf-8'))

        with open('{0}/{1}.cert'.format(path, fname), 'w') as fname_file:
            fname_file.write(cert_pem.decode('utf-8'))


def main():

    # We're not doing anything here yet
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--create-ca', action='store_true',
        default=True,
        help="Create CA along with cert")
    parser.add_argument(
        '--hostname', action='store',
        default='localhost.localdomain',
        help="Hostname to use for certs")
    parser.add_argument(
        '--key-bits', action='store',
        default=4096,
        type=int,
        help="Number of bits to use in the private keys")
    parser.add_argument(
        '--years', action='store',
        default=1,
        type=int,
        help="Number of years that the certs are valid")
    parser.add_argument(
        '-v', '--verbose', action='count', default=0,
        help="Increase verbosity (specify multiple times for more)")
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose >= 1:
        log_level = logging.DEBUG

    format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(format=format, datefmt='%m-%d %H:%M', level=log_level)

    cname = args.hostname
    bits = args.key_bits
    years = args.years
    local_dir = os.path.join(os.getcwd(), cname.replace('.', '-'))
    cert_gen = CertificateGenerator()
    cert_gen.create_local_path(local_dir)

    if args.create_ca:
        ca_data = cert_gen.generate_cert_data(cname, bits, years)
        LOG.info('ca_data {0}'.format(ca_data))
        cert_gen.write_certs(local_dir, **ca_data)
        client_data = cert_gen.generate_cert_data(cname, bits, years,
                                                  **ca_data)
        LOG.info('client_data {0}'.format(client_data))
        cert_gen.write_certs(local_dir, **client_data)


if __name__ == '__main__':
    main()
