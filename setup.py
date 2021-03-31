from setuptools import setup

setup(name='etdisu',
      version='0.1',
      description='extracts bepress metadata from a list of zip files',
      url='http://github.com/wryan14/etdisu',
      author='Ryan Wolfslayer',
      entry_points = {'console_scripts': ['etd=etdisu.etd:main']},
      packages=['etdisu'],
      package_data={'etdisu': ['*.csv', 'data/*.csv',
                               '*.xsl', 'data/*.xsl', '*.jar']},
      install_requires=['lxml==4.6.3', 'numpy==1.18.1', 'pandas==1.0.1',
                        'pathlib==1.0.1', 'pdfminer.six==20200124'],
      )
