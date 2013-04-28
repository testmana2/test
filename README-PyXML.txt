PyXML has a problem calculating the datasize of the data read from an XML file.
In order to correct this, make the adjustment shown below.

Near the end of method parse_xml_decl (in PyXML 0.8.3 this is at line
723) in _xmlplus.parsers.xmlproc.xmlutils:

        try:
            self.data = self.charset_converter(self.data)
            self.datasize = len(self.data)  ### ADD THIS LINE
        except UnicodeError, e:
            self._handle_decoding_error(self.data, e)
        self.input_encoding = enc1

Here is the change as a diff.

--- _xmlplus/parsers/xmlproc/xmlutils.py.orig        2006-11-13 11:30:07.768059659 +0100
+++ _xmlplus/parsers/xmlproc/xmlutils.py     2006-11-13 11:30:38.871925067 +0100
@@ -720,6 +720,7 @@ class XMLCommonParser(EntityParser):
             # to the recoding.
             try:
                 self.data = self.charset_converter(self.data)
+                self.datasize = len(self.data)
             except UnicodeError, e:
                 self._handle_decoding_error(self.data, e)
             self.input_encoding = enc1
