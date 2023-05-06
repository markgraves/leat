## Adding new types of readers
1. Create a reader class, importing from BaseReader, that implements read and/or read_file
2. Update the __init__.py file to try import or create a stub
3. Modify leat.store.core.doc_file to update file extension types, 
4. Modify leat.store.core.doc_store to import class, update supported file types, and add logic to read_document