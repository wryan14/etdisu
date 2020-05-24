import argparse
import sys
from . import etdf, merge_xml


parser = argparse.ArgumentParser(description='Transforms Proquest XML to BePress XML')
parser.add_argument('filename', type=argparse.FileType('r', encoding='iso-8859-1'))


def main():
    args = parser.parse_args()
    print(args.filename.name)
    df = etdf(args.filename.name)
    df = df.sort_values(by='lname', ascending=True).reset_index(drop=True)

    df[~df['Majors Error'].isnull()][['title', 'lname', 'fname', 'Filename',
    'PDFname', 'majors']].to_csv('invalidmajors.csv', header=True,
    index=False)
    merge_xml(df['XMLtext_transformed'].tolist())


if __name__=="__main__":
    sys.exit(main())
