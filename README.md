# UNIFIED-API-POS-DATA-TRANSFORMATION
Implementation of a Multi-Serialized ETL pipeline


Source API's are interfaces built into applications and databases that allow external systems to extract data and Pipeline APIs define how data flows through a pipeline. Source APIs are built as REST and use HTTP methods like GET get to Fetch JSON payloads. Pipeline APIS us JSON to define endpoints, authentication, rules, and object oriented SDKs.

The Pipeline in this project pulled data from multiple APIs, normalized them into a schema and loaded the into a central destination. It used a mapping dictionary during the transform step. This project gave insight on how the Pipeline Architecture Extracts, Transforms, and Loads using SKUs. Avoiding hard coding rules are key!
