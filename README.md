etdisu
=========

Etdisu is a command-line tool that transforms ProQuest XML files into BePress compatible metadata.

Prerequisites
-------------

This project requires java be installed on your computer and accessible through the command line.


Getting Started
----------------

``` {.sourceCode .console}
$ git clone https://github.com/wryan14/etdisu.git
$ cd etdisu
$ pip install .
```

Once successfully installed, run the application as follows:

```{.sourceCode .console}
$ etd /path/to/file/test_docs.zip
```

Output
-------

Running the above command will result in two files: invalidmajors.csv and outfile.xml.  

### invalidmajors.csv

The *invalidmajor* file records any confilct between the input records and the list of majors found in the project's authority file.  To change or update the authority file, you can modify the [ListofMajors.csv](https://github.com/wryan14/etdisu/blob/master/etdisu/data/ListofMajors.csv) located in the data folder of this project.

### outfile.xml

The output, outfile.xml, contains the BePress compatible metadata.  Please note that the transformation is based on an XSLT script put together for Iowa State, so you may need to modify or replace this project's [ProQuest XSLT script](https://github.com/wryan14/etdisu/blob/master/etdisu/data/proquest_transform.xsl).
