#!/usr/bin/env python

"""etd.py: Processes Proquest zip files into BePress compatible XML"""

__author__ = "Ryan Wolfslayer"
__copyright__ = "Copyright 2020, Iowa State University"
__license__ = "GPL"
__version__ = "1.0"

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from lxml import etree

import pandas as pd
import io
import zipfile
import os
import subprocess
import re

# set up variables
directory = os.path.dirname(os.path.abspath(__file__))
sup = os.path.join(directory, 'data')
authority = pd.read_csv(os.path.join(sup, 'ListofMajors.csv'), header=None)

###################################################
# Input helper functions
###################################################

def extract(filename):
    file_list = []
    z = zipfile.ZipFile(filename)
    for f in z.namelist():
        content = io.BytesIO(z.read(f))
        zip_file = zipfile.ZipFile(content)
        file_list.append(zip_file)

    return file_list


def xmltransform(infile, xslt, outfile):
    '''Uses subprocess to run java -jar from command line. saxon9.jar must be
    in the same directory as this script'''
    # sets up path to etdcode/saxon9.jar
    directory = os.path.dirname(os.path.abspath(__file__))
    sax9 = os.path.join(directory, 'saxon9.jar')
    subprocess.call('java -jar ' + '"'+sax9+'" -o' + ' "' +
                    outfile + '" "' + infile + '" "' + xslt+'"')


def pdfconvert(pdf_bytes, pages=[0, 1, 2, 3, 4, 5, 6, 7]):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)
    output = io.StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    infile = io.BytesIO(pdf_bytes)
    [interpreter.process_page(page)
     for page in PDFPage.get_pages(infile, pagenums)]
    infile.close()
    converter.close()
    text = output.getvalue()
    return text


def tabletransform():
    '''
        Get fname, mname, and lname into a pandas table, using XSLT 1.0
    '''
    xslt_root = etree.XML('''
    <xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="/">
        <table border="0">
            <tr>
                <th>title</th>
                <th>lname</th>
                <th>fname</th>
                <th>mname</th>
            </tr>
            <!--TODO: Auto-generate template-->
            <xsl:apply-templates />
        </table>
    </xsl:template>
    <xsl:template match="DISS_submission">
        <tr>
        <td><xsl:value-of select="DISS_description/DISS_title" /></td>
        <td><xsl:value-of select="DISS_authorship/DISS_author/DISS_name/DISS_surname" /></td>
        <td><xsl:value-of select="DISS_authorship/DISS_author/DISS_name/DISS_fname"/> </td>
        <td><xsl:value-of select="DISS_authorship/DISS_author/DISS_name/DISS_middle"/></td>
        </tr>
    </xsl:template>
    </xsl:stylesheet>''')
    return etree.XSLT(xslt_root)

#############################################
# Main imports
#############################################


def dunzip(infile: '.zip'):
    '''Converts Zipfile input into dataframe'''
    input_zip = extract(infile)

    # define variables to store output
    pdf_list, pd_list = [], []

    for count, zip_obj in enumerate(input_zip):
        print('Processing files: {}/{}'.format(count+1, len(input_zip)), end='\r')
        li = {name: zip_obj.read(name) for name in zip_obj.namelist()}
        for k, v in li.items():
            if '.pdf' in k:
                pdf_text = pdfconvert(v)
                pdf_list.append((k, pdf_text))
            elif '.xml' in k:
                root = etree.fromstring(v)
                tmpdf = pd.read_html(str(tabletransform()(root)))[0]
                tmpdf['XMLtext'] = [etree.tostring(root)]
                # uncomment next two lines if columns are not naming properly
                #tmpdf.columns = tmpdf.iloc[0]
                #tmpdf = tmpdf.iloc[1:]
                tmpdf['Filename'] = k
                pd_list.append(tmpdf)
            else:
                pass
    df = pd.concat(pd_list).reset_index(drop=True)
    df['PDFname'] = [pdfname[0] for pdfname in pdf_list]
    df['PDFtext'] = [pdfname[1] for pdfname in pdf_list]

    return df

###################################################
# Dataframe cleaning helper functions
###################################################


def save_and_transform(xml):
    # set up directory
    tmp = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'temp'))
    sup = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
    tmp1 = os.path.join(tmp, 'TEMP.xml')
    tmp2 = os.path.join(tmp, 'TEMPOUT.xml')
    xsltscript = os.path.join(sup, 'proquest_transform.xsl')

    if not os.path.exists(tmp):
        os.mkdir(tmp)

    with open(tmp1, 'wb') as f:
        f.write(xml)

    # use command line to run XSLT 2.0
    xmltransform(tmp1, xsltscript, tmp2)
    root = etree.parse(tmp2)
    return etree.tostring(root)


def findmajor(pdftext):
    majors = []

    for line in pdftext:
        z = re.search(
            r'(?<=Major:).*$|(?<=majors:).*$|(?<=Co-Majors:).*$', line)
        if z != None:
            major = z.group()
            major = (major.strip())
            major = (re.sub(r'\(.*\)', '', str(major)))
            majors.append(major)

    return '; '.join([y.strip() for y in majors])


def flagmajors(xmltext, authoritylist):
    root = etree.fromstring(xmltext)
    major = root.xpath('//field[@name="major"]/value/text()')
    for x in major:
        if x not in authoritylist:
            return 'Invalid Major'
        else:
            return None


def add_field(xmltext, fieldname, value_text):
    root = etree.fromstring(xmltext)
    fields = root.xpath('//fields')

    # remove field if exists
    for bad in root.xpath("//fields/field[@name='{}']".format(fieldname)):
        bad.getparent().remove(bad)

    field = etree.SubElement(fields[0], 'field')
    field.set('type', 'string')
    field.set('name', fieldname)

    for m in [v.strip() for v in value_text.split(';')]:
        value = etree.SubElement(field, 'value')
        value.text = m

    return etree.tostring(root)

###################################################
# XML output function
###################################################


def merge_xml(xml_list, file='outfile.xml'):
    '''Merge list of XML making document a subelement of documents'''
    root = etree.fromstring(xml_list[0])
    for idx, xml in enumerate(xml_list[1:]):
        subelem = etree.fromstring(xml)
        subelem = subelem.xpath('/documents/document')[0]
        root.insert(idx+1, subelem)

    with open(file, 'wb') as f:
        f.write(etree.tostring(root, xml_declaration=True,
                               encoding='iso-8859-1', method='xml'))

###################################################
# Import for command line application
###################################################

def etdf(infile: 'zip file'):
    '''Converts zip file into dataframe'''

    if '.zip' not in infile:
        print('Please upload a zipfile')

    df = dunzip(infile)
    df['XMLtext_transformed'] = df['XMLtext'].apply(
        lambda x: save_and_transform(x))

    # find majors from PDF
    df['majors'] = df['PDFtext'].apply(lambda x: findmajor(x.split('\n')))
    df['XMLtext_transformed'] = df.apply(lambda x: add_field(
        x.XMLtext_transformed, 'major',  x.majors), axis=1)
    df = df.fillna('NONE')
    df['XMLtext_transformed'] = df.apply(lambda x: add_field(x.XMLtext_transformed, 'rights_holder',
                                                             ' '.join([str(y).strip() for y in [x.fname.title(), x.mname.title(), x.lname.title()] if y != 'NONE'.title()])), axis=1)
    df['Majors Error'] = df['XMLtext_transformed'].apply(
        lambda x: flagmajors(x, authority[0].tolist()))

    return df
