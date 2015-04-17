#!/usr/bin/env python3

"""Verify ORTOFON .eaf transcript according to XML schema and additional
constraints.

"""

import sys
import pdb

from lxml import etree

class VerificationError(Exception):
    def __init__(self, error_log):
        self.error_log = error_log

    def __str__(self):
        return "  " + "\n  ".join(self.error_log)

def verify(tree):
    """Run all post-validation verification checks.

    """
    errors = []

    for check in (vocab_meta, vocab_META, tier_attribs, hierarchy):
        try:
            check(tree)
        except VerificationError as e:
            errors += e.error_log

    if errors:
        raise VerificationError(errors)

def vocab_meta(tree):
    """Verify that meta tiers only have entries allowed by the constrained
    vocabulary.

    """

    vocab = set([
        "citoslovce",
        "citoslovce odporu",
        "citoslovce opovržení",
        "citoslovce údivu",
        "citoslovce úleku",
        "dlouhá pauza",
        "hvízdání",
        "kašel",
        "klepání",
        "kýchání",
        "lusknutí prsty",
        "líbání",
        "mlasknutí",
        "mluví ke zvířeti",
        "nadechnutí",
        "odkašlání",
        "plácnutí",
        "pláč",
        "polknutí",
        "pousmání",
        "povzdech",
        "pískání",
        "říhnutí",
        "smrkání",
        "smích",
        "srkání",
        "škytání",
        "tleskání",
        "vydechnutí",
        "zakoktání",
        "zívání"
    ])
    errors = []

    for meta in tree.xpath("//TIER[@LINGUISTIC_TYPE_REF = 'meta']//ANNOTATION_VALUE/text()"):
        if meta not in vocab:
            errors.append("'{}' is not allowed in a meta tier.".format(meta))

    if errors:
        raise VerificationError(errors)

def vocab_META(tree):
    """Verify that META tier only has entries allowed by the constrained
    vocabulary.

    """

    vocab = set([
        "cinkání nádobí",
        "dlouhá pauza",
        "domácí spotřebič",
        "hlasitý hovor v pozadí",
        "hluk v pozadí",
        "hra na hudební nástroj",
        "jiné zvíře",
        "klepání",
        "kroky",
        "mňoukání kočky",
        "nesrozumitelný hovor více mluvčích najednou",
        "nábytek",
        "pláč dítěte",
        "počítač a příslušenství",
        "ruch z ulice",
        "rušivý zvuk",
        "smích více mluvčích najednou",
        "štěkání psa",
        "zvonění telefonu",
        "zvuk z rádia",
        "zvuk z televize",
        "zvuky při jídle"
    ])
    errors = []

    for meta in tree.xpath("//TIER[@LINGUISTIC_TYPE_REF = 'META']//ANNOTATION_VALUE/text()"):
        if meta not in vocab:
            errors.append("'{}' is not allowed in a META tier.".format(meta))

    if errors:
        raise VerificationError(errors)

def tier_attribs(tree):
    """Verify that the tier attributes are consistent and conform to
    requirements.

    """
    errors = []

    if tree.xpath("//TIER[@LINGUISTIC_TYPE_REF = 'fonetický' and not(@PARENT_REF)]"):
        errors.append("TIERs with @LINGUISTIC_TYPE_REF = 'fonetický' should have a @PARENT_REF attribute.")

    for fon_tier in tree.xpath("//TIER[@LINGUISTIC_TYPE_REF = 'fonetický']"):
        tier_id_prefix = fon_tier.attrib["TIER_ID"].split(" ")[0]
        parent_ref_prefix = fon_tier.attrib["PARENT_REF"].split(" ")[0]
        if not tier_id_prefix == parent_ref_prefix:
            errors.append("The numeric prefixes of @TIER_ID and @PARENT_REF on a TIER with @LINGUISTIC_TYPE_REF = 'fonetický' should match.")

    if errors:
        raise VerificationError(errors)

def hierarchy(tree):
    """Verify that some forbidden nesting of elements does not occur.

    """
    errors = []

    if tree.xpath("//TIER[@PARENT_REF]//ALIGNABLE_ANNOTATION"):
        errors.append("ALIGNABLE_ANNOTATIONs are not allowed on a TIER with a @PARENT_REF attribute.")

    if errors:
        raise VerificationError(errors)

schema_root = etree.parse("EAFv2.7_UCNK.xsd").getroot()
schema = etree.XMLSchema(schema_root)
ERRORS = False

for f in sys.argv[1:]:
    try:
        tree = etree.parse(f)
        schema.assertValid(tree)
    except etree.XMLSyntaxError as e:
        # syntax error → file cannot be parsed → jump to next iteration
        # (additional verifications don't make sense if file cannot be parsed)
        ERRORS = True
        sys.stderr.write("File {} is malformed XML.\n".format(f))
        continue
    except etree.DocumentInvalid as validation_errors:
        ERRORS = True
        sys.stderr.write("Validation error(s) in {}:\n  ".format(f))
        sys.stderr.write("\n  ".join(map(str, validation_errors.error_log)))
        sys.stderr.write("\n")

    try:
        verify(tree)
    except VerificationError as e:
        ERRORS = True
        sys.stderr.write("Verification error(s) in {}:\n{}\n".format(f, str(e)))

if ERRORS:
    sys.stderr.write("""
###############################################################################
Please correct the errors listed above and re-run the validation, new ones may
appear.
""")
else:
    sys.stderr.write("""
###############################################################################
Validation completed. No errors were found.
""")
