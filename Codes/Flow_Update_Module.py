"""
This script compares identifies and updates changes in unique identifiers
"""

import os
import pandas as pd

# -------------------------------------------
# Define Input Folders
# -------------------------------------------

input_folders = [
   '',
   ''
]

# -------------------------------------------
# Function to load data from files
# -------------------------------------------

def load_data(folder_name):
    stop_times_path = os.path.join(folder_name, 'stop_times.txt')
    trips_path = os.path.join(folder_name, 'trips.txt')
    stops_path = os.path.join(folder_name, 'stops.txt')
    calD_path = os.path.join(folder_name, 'calendar_dates.txt')
    cal_path = os.path.join(folder_name, 'calendar.txt')
    agency_path = os.path.join(folder_name, 'agency.txt')
    routes_path = os.path.join(folder_name, 'routes.txt')
    shapes_path = os.path.join(folder_name, 'shapes.txt')
    
    stop_times = pd.read_csv(stop_times_path)
    trips = pd.read_csv(trips_path)
    stops = pd.read_csv(stops_path)
    calD = pd.read_csv(calD_path)
    cal = pd.read_csv(cal_path)
    agency = pd.read_csv(agency_path)
    routes = pd.read_csv(routes_path)
    shapes = pd.read_csv(shapes_path)
    
    return stop_times, trips, stops, calD, cal, agency, routes, shapes

# -------------------------------------------
# Functions to detect changes in unique identifiers
# -------------------------------------------

def detect_service_id_changes(cal1, cal2):
    merged_cal = pd.merge(cal1, cal2, on=list(cal1.columns.difference(['service_id'])), suffixes=('_feed1', '_feed2'), how='outer')
    service_id_mapping = merged_cal[['service_id_feed1', 'service_id_feed2']].dropna()
    return dict(zip(service_id_mapping['service_id_feed1'], service_id_mapping['service_id_feed2']))

def detect_trip_id_changes(trips1, trips2):
    trip_id_change_map = {}
    trips2_indexed = trips2.set_index(['route_id', 'service_id', 'trip_id'])
    
    for _, row1 in trips1.iterrows():
        key = (row1['route_id'], row1['service_id'], row1['trip_id'])
        if key in trips2_indexed.index:
            # Trip IDs are identical, no change needed.
            continue
        else:
            # Check for matching route_id and service_id but different trip_id
            matching_trips = trips2[
                (trips2['route_id'] == row1['route_id']) &
                (trips2['service_id'] == row1['service_id'])
            ]
            if len(matching_trips) == 1:
                new_trip_id = matching_trips.iloc[0]['trip_id']
                trip_id_change_map[row1['trip_id']] = new_trip_id

    return trip_id_change_map


def detect_stop_id_changes(stops1, stops2):
    common_columns = list(stops1.columns.difference(['stop_id']))
    merged_stops = pd.merge(stops1, stops2, on=common_columns, suffixes=('_feed1', '_feed2'), how='outer')
    stop_id_mapping = merged_stops[['stop_id_feed1', 'stop_id_feed2']].dropna()
    return dict(zip(stop_id_mapping['stop_id_feed1'], stop_id_mapping['stop_id_feed2']))

def detect_route_id_changes(routes1, routes2):
    common_columns = list(routes1.columns.difference(['route_id']))
    merged_routes = pd.merge(routes1, routes2, on=common_columns, suffixes=('_feed1', '_feed2'), how='outer')
    route_id_mapping = merged_routes[['route_id_feed1', 'route_id_feed2']].dropna()
    return dict(zip(route_id_mapping['route_id_feed1'], route_id_mapping['route_id_feed2']))

def detect_shape_id_changes(shapes1, shapes2):
    shape_id_mapping = {}

    # Generate CSV representations of shapes from feed2
    shapes2_groups = {
        shape_id: group[['shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence']].to_csv(index=False)
        for shape_id, group in shapes2.groupby('shape_id')
    }

    # Compare each shape from feed1 to shapes in feed2
    for shape_id1, group1 in shapes1.groupby('shape_id'):
        shape1_csv = group1[['shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence']].to_csv(index=False)

        matched = False
        for shape_id2, shape2_csv in shapes2_groups.items():
            if shape1_csv == shape2_csv:
                # Identical shapes; retain original ID
                shape_id_mapping[shape_id1] = shape_id1
                matched = True
                break

        if not matched:
            # No identical match found; shape_id remains unchanged
            pass

    return shape_id_mapping


# -------------------------------------------
# Updating Functions
# -------------------------------------------

def update_service_ids_in_calendar_dates(calendar_dates, service_id_mapping):
    calendar_dates['service_id'] = calendar_dates['service_id'].replace(service_id_mapping)
    return calendar_dates

def update_service_ids_in_trips(trips, service_id_mapping):
    trips['service_id'] = trips['service_id'].replace(service_id_mapping)
    return trips

def update_route_ids_in_trips(trips, route_id_mapping):
    trips['route_id'] = trips['route_id'].replace(route_id_mapping)
    return trips

def update_shape_ids_in_trips(trips, shape_id_mapping):
    trips['shape_id'] = trips['shape_id'].replace(shape_id_mapping)
    return trips

def update_stop_times_ids(stop_times, trip_id_mapping, stop_id_mapping):
    stop_times['trip_id'] = stop_times['trip_id'].replace(trip_id_mapping)
    stop_times['stop_id'] = stop_times['stop_id'].replace(stop_id_mapping)
    return stop_times

# -------------------------------------------
# Trips Verification Process
# -------------------------------------------

def verify_trips(feed1_stop_times, feed2_stop_times, feed1_trips, feed2_trips):
    print("\nStarting trips verification...")
    identical_trips = []
    changed_identical_trips = []
    different_trips = []

    trip_id_changes = detect_trip_id_changes(feed1_trips, feed2_trips)

    for trip_id1 in feed1_trips["trip_id"]:
        trip_id2 = trip_id_changes.get(trip_id1, trip_id1)

        stop_times1 = feed1_stop_times[feed1_stop_times["trip_id"] == trip_id1]
        stop_times2 = feed2_stop_times[feed2_stop_times["trip_id"] == trip_id2]

        are_identical = stop_times1.equals(stop_times2)
        if are_identical:
            if trip_id1 == trip_id2:
                identical_trips.append(trip_id1)
            else:
                changed_identical_trips.append((trip_id1, trip_id2))
        else:
            different_trips.append(trip_id1)

    print("\nComparison Results:")
    print("Identical trips:")
    for trip in identical_trips:
        print(f"Trip with trip_id '{trip}' is identical in both feeds.")

    print("\nTrips with trip_id changes:")
    for old_id, new_id in changed_identical_trips:
        print(f"Trip with trip_id '{old_id}' in Feed 1 is identical to '{new_id}' in Feed 2.")

    print("\nActually different trips:")
    for trip in different_trips:
        print(f"Trip with trip_id '{trip}' in Feed 1 is different.")

    return identical_trips, changed_identical_trips, different_trips

# -------------------------------------------
# Main Execution Logic
# -------------------------------------------

stop_times_list, trips_list, stops_list, calendar_dates_list, calendars_list, agency_list, routes_list, shapes_list = [], [], [], [], [], [], [], []
for folder in input_folders:
    stop_times, trips, stops, calD, cal, agency, routes, shapes = load_data(folder)
    stop_times_list.append(stop_times)
    trips_list.append(trips)
    stops_list.append(stops)
    calendar_dates_list.append(calD)
    calendars_list.append(cal)
    agency_list.append(agency)
    routes_list.append(routes)
    shapes_list.append(shapes)

service_id_changes = detect_service_id_changes(calendars_list[0], calendars_list[1])
for i in range(len(calendar_dates_list)):
    calendar_dates_list[i] = update_service_ids_in_calendar_dates(calendar_dates_list[i], service_id_changes)

trip_id_changes = detect_trip_id_changes(trips_list[0], trips_list[1])
stop_id_changes = detect_stop_id_changes(stops_list[0], stops_list[1])
route_id_changes = detect_route_id_changes(routes_list[0], routes_list[1])
shape_id_changes = detect_shape_id_changes(shapes_list[0], shapes_list[1])

stop_times_list[1] = update_stop_times_ids(stop_times_list[1], trip_id_changes, stop_id_changes)
trips_list[1] = update_shape_ids_in_trips(trips_list[1], shape_id_changes)

# Perform trips verification process
identical_trips, changed_identical_trips, different_trips = verify_trips(
    stop_times_list[0], stop_times_list[1], trips_list[0], trips_list[1]
)

# Ask user whether to proceed with the rest of the code
proceed = input("\nVerification complete. Do you want to proceed with the rest of the process? (yes/no): ").strip().lower()
if proceed != "yes":
    print("Process terminated by user.")
else:
    # Update trips, routes, etc., and save to output
    for i in range(len(trips_list)):
        trips_list[i] = update_service_ids_in_trips(trips_list[i], service_id_changes)
        trips_list[i] = update_route_ids_in_trips(trips_list[i], route_id_changes)

    output_folder = ''
    calendar_dates_list[1].to_csv(os.path.join(output_folder, 'calendar_dates.txt'), index=False)
    calendars_list[1].to_csv(os.path.join(output_folder, 'calendar.txt'), index=False)
    stops_list[1].to_csv(os.path.join(output_folder, 'stops.txt'), index=False)
    trips_list[1].to_csv(os.path.join(output_folder, 'trips.txt'), index=False)
    stop_times_list[1].to_csv(os.path.join(output_folder, 'stop_times.txt'), index=False)
    routes_list[1].to_csv(os.path.join(output_folder, 'routes.txt'), index=False)
    shapes_list[1].to_csv(os.path.join(output_folder, 'shapes.txt'), index=False)
    agency_list[1].to_csv(os.path.join(output_folder, 'agency.txt'), index=False)
    print("Updated files saved in specified output folder.")
