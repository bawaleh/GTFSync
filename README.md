# GTFSync

GTFSync is a Python-based tool designed to detect changes, update identifiers, and merge GTFS (General Transit Feed Specification) datasets across time periods. It simplifies the process of maintaining clean and consistent GTFS data by automating comparison, synchronization, and integration workflows.

## Core Modules

GTFSync is composed of three modular tools:

- **Transit Detect Module**  
  Compares two GTFS feeds file-by-file to detect added, removed, or modified entries. Offers high-level, mid-level, and detailed summaries.

- **Flow Update Module**  
  Scans and updates identifiers such as `trip_id`, `route_id`, `stop_id`, `shape_id`, and `service_id` across related GTFS files to ensure synchronization between feeds.

- **Seamless Merge Module**  
  Merges multiple GTFS feeds into a single unified feed, appending suffixes to identifiers to prevent duplication and maintain data integrity.

## System Requirements

- Python 3.7 or higher
- `pandas` library (install with `pip install pandas`)
- Standard libraries used: `os`, `collections`, `difflib`

No external dependencies or installations beyond Python are required.

## Documentation 
-Full usage instructions, screenshots, and step-by-step examples are available in the GTFSync_User_Guide.pdf.
