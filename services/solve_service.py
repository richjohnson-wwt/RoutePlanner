"""
Service for solving VRPTW (Vehicle Routing Problem with Time Windows) using Google OR-Tools.
"""
from __future__ import annotations

import math
from pathlib import Path
from datetime import datetime
from models.problem_state import ProblemState
from models.route import Route

try:
    from ortools.constraint_solver import routing_enums_pb2
    from ortools.constraint_solver import pywrapcp
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False


class SolveService:
    """Service for solving VRPTW optimization problems."""
    
    def __init__(self, time_limit_seconds: int = 30):
        """
        Initialize the solve service.
        
        Args:
            time_limit_seconds: Maximum time to spend solving (default: 30 seconds)
        """
        if not ORTOOLS_AVAILABLE:
            raise ImportError(
                "Google OR-Tools is not installed. "
                "Install it with: pip install ortools"
            )
        self.time_limit_seconds = time_limit_seconds
    
    def solve_problem(
        self,
        problem: ProblemState,
        per_cluster: bool = True,
        service_time_hours: float = 0.5,
        speed_mph: float = 50.0,
        log_callback=None
    ) -> list[Route]:
        """
        Solve VRPTW for the given problem state using Google OR-Tools.
        
        Args:
            problem: ProblemState with clustered sites
            per_cluster: If True, solve each cluster separately. If False, solve whole state.
            service_time_hours: Time spent at each site (in hours)
            speed_mph: Average vehicle speed in miles per hour
            log_callback: Optional callback function for logging messages
            
        Returns:
            List of Route objects representing the solution
            
        Raises:
            RuntimeError: If problem cannot be solved
        """
        def log(msg: str):
            """Helper to log messages"""
            if log_callback:
                log_callback(msg)
        
        if not problem.sites:
            raise RuntimeError(
                "No sites loaded. Please go to the Sites tab and load sites first, "
                f"or ensure sites.csv exists for {problem.client}/{problem.workspace}/{problem.state_code}"
            )
        
        # Filter sites by state
        state_sites = [s for s in problem.sites if s.state_code == problem.state_code]
        
        if not state_sites:
            raise RuntimeError(
                f"No sites found for state {problem.state_code}. "
                f"Loaded {len(problem.sites)} sites but none match state '{problem.state_code}'. "
                "Please check that your sites have the correct state_code."
            )
        
        log(f"Starting VRPTW solve for {len(state_sites)} sites in {problem.state_code}")
        log(f"Mode: {'Per Cluster' if per_cluster else 'Whole State'}")
        log(f"Service Time: {service_time_hours} hours per site")
        log(f"Average Speed: {speed_mph} MPH")
        
        routes = []
        
        if per_cluster:
            # Solve each cluster separately
            if not problem.clusters:
                raise RuntimeError("No clusters found. Please cluster sites first.")
            
            log(f"Solving {len(problem.clusters)} clusters separately...")
            
            for cluster_id, cluster_sites in sorted(problem.clusters.items()):
                # Filter cluster sites by state
                cluster_state_sites = [s for s in cluster_sites if s.state_code == problem.state_code]
                
                if not cluster_state_sites:
                    log(f"Cluster {cluster_id}: No sites in {problem.state_code}, skipping")
                    continue
                
                log(f"Cluster {cluster_id}: Solving {len(cluster_state_sites)} sites...")
                
                # Solve this cluster using OR-Tools (may return multiple routes/vehicles)
                cluster_routes = self._solve_single_route(
                    state_code=problem.state_code,
                    cluster_id=cluster_id,
                    sites=cluster_state_sites,
                    service_time_hours=service_time_hours,
                    speed_mph=speed_mph,
                    log_callback=log
                )
                
                if cluster_routes:
                    routes.extend(cluster_routes)
                    total_stops = sum(r.stops for r in cluster_routes)
                    total_hours = sum(r.service_hours for r in cluster_routes)
                    log(f"Cluster {cluster_id}: Generated {len(cluster_routes)} route(s), {total_stops} stops, {total_hours:.2f} hours")
                else:
                    log(f"Cluster {cluster_id}: Failed to find solution")
        else:
            # Solve whole state as one problem
            log(f"Solving whole state ({len(state_sites)} sites) as single problem...")
            
            state_routes = self._solve_single_route(
                state_code=problem.state_code,
                cluster_id=0,
                sites=state_sites,
                service_time_hours=service_time_hours,
                speed_mph=speed_mph,
                log_callback=log
            )
            
            if state_routes:
                routes.extend(state_routes)
                total_stops = sum(r.stops for r in state_routes)
                total_hours = sum(r.service_hours for r in state_routes)
                log(f"Generated {len(state_routes)} route(s), {total_stops} stops, {total_hours:.2f} hours")
            else:
                log("Failed to find solution")
        
        if not routes:
            raise RuntimeError("No valid routes found. Solver failed to find a solution.")
        
        log(f"Solve complete: Generated {len(routes)} route(s)")
        
        # Save results
        if problem.paths:
            self._save_solution(problem, routes, log_callback=log)
        
        return routes
    
    def _solve_single_route(
        self,
        state_code: str,
        cluster_id: int,
        sites: list,
        service_time_hours: float,
        speed_mph: float,
        log_callback=None
    ) -> Route | None:
        """
        Solve a single route using Google OR-Tools TSP solver.
        
        Args:
            state_code: State code for the route
            cluster_id: Cluster ID for the route
            sites: List of sites to visit
            service_time_hours: Service time per site in hours
            speed_mph: Average vehicle speed in MPH
            log_callback: Optional logging callback
            
        Returns:
            Route object with optimized solution, or None if no solution found
        """
        def log(msg: str):
            if log_callback:
                log_callback(msg)
        
        if len(sites) < 2:
            # Single site or empty - just return in order
            return [Route(
                state_code=state_code,
                cluster_id=cluster_id,
                vehicle_id=1,
                stops=len(sites),
                sequence=[s.id for s in sites],
                mode="trivial",
                speed_mph=speed_mph,
                service_hours=len(sites) * service_time_hours,
                solved_at=datetime.now()
            )]
        
        # Create distance matrix
        distance_matrix = self._create_distance_matrix(sites)
        
        # Calculate number of vehicles needed based on time constraints
        # Estimate: 480 min window / (service_time + avg_travel_time per site)
        service_time_minutes = int(service_time_hours * 60)
        # Rough estimate: assume 15 min average travel between sites
        time_per_site = service_time_minutes + 15
        max_sites_per_vehicle = max(1, int(420 / time_per_site))  # Use 420 min (7 hours) to be safe
        num_vehicles = max(1, (len(sites) + max_sites_per_vehicle - 1) // max_sites_per_vehicle)
        
        if log_callback:
            log_callback(f"  Estimated {num_vehicles} vehicle(s) needed for {len(sites)} sites")
        
        # Create routing index manager with multiple vehicles
        # All vehicles start and end at the depot (first site)
        manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix),
            num_vehicles,  # Number of vehicles
            0   # Depot index (start at first site)
        )
        
        # Create routing model
        routing = pywrapcp.RoutingModel(manager)
        
        # Create distance callback
        def distance_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return int(distance_matrix[from_node][to_node])
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        
        # Define cost of each arc
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add time dimension with time windows
        # Convert service time from hours to minutes
        service_time_minutes = int(service_time_hours * 60)
        
        # Create time callback that includes both travel time AND service time
        def time_callback(from_index, to_index):
            """Returns the time between two nodes including travel and service time."""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            # Calculate travel time: distance / speed (convert to minutes)
            travel_time = (distance_matrix[from_node][to_node] / speed_mph) * 60
            # Add service time at the departure node (from_node)
            # This ensures we spend service_time at each location before leaving
            return int(travel_time + service_time_minutes)
        
        time_callback_index = routing.RegisterTransitCallback(time_callback)
        
        # Add time dimension
        # Time windows: 9am (0 min) to 5pm (480 min = 8 hours)
        time_dimension_name = 'Time'
        routing.AddDimension(
            time_callback_index,
            60,  # Allow waiting time (slack) of up to 60 minutes
            480,  # Maximum time per vehicle (8 hours: 9am to 5pm)
            False,  # Don't force start cumul to zero
            time_dimension_name
        )
        time_dimension = routing.GetDimensionOrDie(time_dimension_name)
        
        # Add time window constraints for each location
        # All sites must be visited (arrival time) between 9am (0) and 5pm (480 minutes)
        for location_idx in range(len(sites)):
            index = manager.NodeToIndex(location_idx)
            # Time window: must arrive between 0 (9am) and 480 (5pm)
            time_dimension.CumulVar(index).SetRange(0, 480)
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = self.time_limit_seconds
        
        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)
        
        if not solution:
            if log_callback:
                log_callback("  No solution found - problem may be infeasible")
            return []
        
        # Extract solution with actual times from solver
        # Get time dimension to extract actual arrival times
        time_dimension = routing.GetDimensionOrDie('Time')
        
        routes = []
        
        # Extract route for each vehicle
        for vehicle_id in range(num_vehicles):
            index = routing.Start(vehicle_id)
            sequence = []
            total_distance_miles = 0
            
            # Get the depot node (starting point)
            depot_node = manager.IndexToNode(index)
            
            # Add depot to sequence - it's a site that needs to be visited
            sequence.append(sites[depot_node].id)
            
            # Move to next node
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            
            # Visit all remaining nodes in the route
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                sequence.append(sites[node].id)
                
                # Calculate distance from previous to current
                total_distance_miles += distance_matrix[manager.IndexToNode(previous_index)][manager.IndexToNode(index)]
                
                previous_index = index
                index = solution.Value(routing.NextVar(index))
            
            # Skip empty routes (vehicle not used)
            if len(sequence) == 0:
                continue
            
            # Get actual total time from the solver (in minutes)
            # This is the time at the last node visited for this vehicle
            final_index = routing.Start(vehicle_id)
            last_index = final_index
            while not routing.IsEnd(final_index):
                last_index = final_index
                final_index = solution.Value(routing.NextVar(final_index))
            
            final_time_var = time_dimension.CumulVar(last_index)
            total_time_minutes = solution.Value(final_time_var)
            total_hours = total_time_minutes / 60.0
            
            routes.append(Route(
                state_code=state_code,
                cluster_id=cluster_id,
                vehicle_id=vehicle_id + 1,  # 1-indexed
                stops=len(sequence),
                sequence=sequence,
                mode="ortools",
                speed_mph=speed_mph,
                service_hours=total_hours,
                solved_at=datetime.now()
            ))
        
        return routes
    
    def _create_distance_matrix(self, sites: list) -> list[list[float]]:
        """
        Create a distance matrix between all sites using Haversine formula.
        
        Args:
            sites: List of sites with lat/lng coordinates
            
        Returns:
            2D matrix of distances in miles
        """
        n = len(sites)
        matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = self._haversine_distance(
                        sites[i].lat, sites[i].lng,
                        sites[j].lat, sites[j].lng
                    )
        
        return matrix
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth.
        
        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point
            
        Returns:
            Distance in miles
        """
        # Earth radius in miles
        R = 3959.0
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def generate_solution_table_data(self, problem: ProblemState, routes: list[Route]) -> list[list[str]]:
        """
        Generate solution table data with stop-by-stop details.
        
        Args:
            problem: ProblemState with sites
            routes: List of routes to process
            
        Returns:
            List of rows, where each row is a list of strings:
            [route_id, stop_sequence, site_id, cluster_id, vehicle_id, lat, lng,
             arrival_time, departure_time, service_time_min, travel_time_min, distance_miles]
        """
        from datetime import datetime, timedelta
        
        table_data = []
        site_lookup = {s.id: s for s in problem.sites}
        
        for route_idx, route in enumerate(routes, 1):
            # Start time for this route (9:00 AM)
            current_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
            
            # Get service time in minutes (convert from hours)
            service_time_minutes = (route.service_hours / len(route.sequence)) * 60 if route.sequence else 0
            
            for stop_seq, site_id in enumerate(route.sequence):
                site = site_lookup.get(site_id)
                
                # Calculate travel time and distance to next stop
                travel_time_min = ""
                distance_miles = ""
                if stop_seq < len(route.sequence) - 1:
                    next_site_id = route.sequence[stop_seq + 1]
                    next_site = site_lookup.get(next_site_id)
                    if site and next_site and site.lat and site.lng and next_site.lat and next_site.lng:
                        distance = self._haversine_distance(site.lat, site.lng, next_site.lat, next_site.lng)
                        travel_time = (distance / route.speed_mph) * 60  # Convert to minutes
                        travel_time_min = f"{travel_time:.2f}"
                        distance_miles = f"{distance:.2f}"
                
                # Calculate times
                arrival_time_str = current_time.strftime("%I:%M %p")
                departure_time = current_time + timedelta(minutes=service_time_minutes)
                departure_time_str = departure_time.strftime("%I:%M %p")
                
                # Create row
                row = [
                    str(route_idx),                                                    # route_id
                    str(stop_seq),                                                     # stop_sequence
                    site_id,                                                           # site_id
                    str(route.cluster_id),                                            # cluster_id
                    str(route.vehicle_id),                                            # vehicle_id
                    f"{site.lat:.6f}" if site and site.lat else "",                  # lat
                    f"{site.lng:.6f}" if site and site.lng else "",                  # lng
                    arrival_time_str,                                                  # arrival_time
                    departure_time_str,                                                # departure_time
                    f"{service_time_minutes:.1f}",                                    # service_time_min
                    travel_time_min,                                                   # travel_time_min
                    distance_miles                                                     # distance_miles
                ]
                table_data.append(row)
                
                # Update current time for next stop
                if travel_time_min:
                    current_time = departure_time + timedelta(minutes=float(travel_time_min))
                else:
                    current_time = departure_time
        
        return table_data
    
    def _save_solution(self, problem: ProblemState, routes: list[Route], log_callback=None) -> None:
        """
        Save solution to CSV file with stop-by-stop details.
        
        Args:
            problem: ProblemState with solution
            routes: List of routes to save
            log_callback: Optional logging callback
        """
        import csv
        
        def log(msg: str):
            if log_callback:
                log_callback(msg)
        
        solution_path = problem.paths.solution_csv()
        
        # Ensure parent directory exists
        solution_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate table data using the shared method
        table_data = self.generate_solution_table_data(problem, routes)
        
        # Write solution CSV with stop-by-stop details
        with open(solution_path, 'w', newline='') as csvfile:
            fieldnames = [
                'route_id', 'stop_sequence', 'site_id', 'cluster_id', 'vehicle_id',
                'lat', 'lng', 'arrival_time', 'departure_time',
                'service_time_min', 'travel_time_min', 'distance_miles'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write each row
            for row in table_data:
                writer.writerow({
                    'route_id': row[0],
                    'stop_sequence': row[1],
                    'site_id': row[2],
                    'cluster_id': row[3],
                    'vehicle_id': row[4],
                    'lat': row[5],
                    'lng': row[6],
                    'arrival_time': row[7],
                    'departure_time': row[8],
                    'service_time_min': row[9],
                    'travel_time_min': row[10],
                    'distance_miles': row[11]
                })
        
        log(f"Solution saved to {solution_path}")
        
        # Update problem state
        problem.routes = routes
        from models.planning_stage import PlanningStage
        problem.stage = PlanningStage.SOLVED
