import json
from datetime import datetime, timedelta
from collections import defaultdict

class SatelliteMonitor:
    """
    A class to monitor satellite telemetry data and generate alerts based on violation conditions.
    
    The system tracks two types of violations:
    1. Three battery voltage readings under the red low limit within 5 minutes
    2. Three thermostat readings exceeding the red high limit within 5 minutes
    """
    
    def __init__(self):
        """
        Initialize the monitor with data structures to track readings and alerts.
        """
        # Dictionary to store recent readings for each satellite and component
        self.readings = defaultdict(list)
        
        # List to store generated alerts
        self.alerts = []
        
        # Time window for violation checks (5 minutes)
        self.time_window = timedelta(minutes=5)
    
    def parse_line(self, line):
        """
        Parse a single line of telemetry data.
        
        Args:
            line (str): A pipe-delimited telemetry record
            
        Returns:
            dict: Parsed telemetry data with fields as keys
        """
        fields = line.strip().split('|')
        return {
            'timestamp': fields[0],
            'satelliteId': int(fields[1]),
            'red_high_limit': float(fields[2]),
            'yellow_high_limit': float(fields[3]),
            'yellow_low_limit': float(fields[4]),
            'red_low_limit': float(fields[5]),
            'raw_value': float(fields[6]),
            'component': fields[7]
        }
    
    def process_telemetry(self, data):
        """
        Process telemetry data and check for violation conditions.
        
        Args:
            data (dict): Parsed telemetry data
        """
        # Convert timestamp to datetime object for comparison
        try:
            timestamp = datetime.strptime(data['timestamp'], '%Y%m%d %H:%M:%S.%f')
        except ValueError:
            # Handle slightly different format if needed
            timestamp = datetime.strptime(data['timestamp'], '%Y%m%d %H:%M:%S')
        
        # Create a key for this satellite and component
        key = (data['satelliteId'], data['component'])
        
        # Add the current reading to our tracking
        self.readings[key].append({
            'timestamp': timestamp,
            'value': data['raw_value'],
            'limit': data['red_high_limit'] if data['component'] == 'TSTAT' else data['red_low_limit'],
            'original_timestamp': data['timestamp']  # Keep original for output
        })
        
        # Check for violations
        self.check_violations(key)
    
    def check_violations(self, key):
        """
        Check for violation conditions for a specific satellite and component.
        
        Args:
            key (tuple): (satelliteId, component) pair identifying which readings to check
        """
        satellite_id, component = key
        readings = self.readings[key]
        
        # Determine the threshold condition based on component type
        if component == 'TSTAT':
            # For thermostat, we check for values exceeding red high limit
            violating_readings = [
                r for r in readings 
                if r['value'] > r['limit']
            ]
            severity = 'RED HIGH'
        elif component == 'BATT':
            # For battery, we check for values below red low limit
            violating_readings = [
                r for r in readings 
                if r['value'] < r['limit']
            ]
            severity = 'RED LOW'
        else:
            # Unknown component, skip
            return
        
        # If we have at least 3 violating readings, check their timestamps
        if len(violating_readings) >= 3:
            # Sort readings by timestamp
            violating_readings.sort(key=lambda x: x['timestamp'])
            
            # Check all possible triplets in the violating readings
            for i in range(len(violating_readings) - 2):
                # Get three consecutive violating readings
                r1 = violating_readings[i]
                r2 = violating_readings[i + 2]  # Skip one to ensure we have 3 within window
                
                # Check if these three are within the 5-minute window
                if (r2['timestamp'] - r1['timestamp']) <= self.time_window:
                    # Found a violation - create alert with the first timestamp
                    alert = {
                        'satelliteId': satellite_id,
                        'severity': severity,
                        'component': component,
                        'timestamp': r1['original_timestamp']
                    }
                    
                    # Add to alerts if not already present (avoid duplicates)
                    if alert not in self.alerts:
                        self.alerts.append(alert)
                    
                    # No need to check other triplets for this violation
                    break
    
    def process_file(self, filename):
        """
        Process a telemetry data file and generate alerts.
        
        Args:
            filename (str): Path to the input file
        """
        with open(filename, 'r') as file:
            for line in file:
                # Skip empty lines
                if not line.strip():
                    continue
                
                # Parse and process each line
                data = self.parse_line(line)
                self.process_telemetry(data)
    
    def get_alerts(self):
        """
        Get the generated alerts in JSON format.
        
        Returns:
            str: JSON string of alerts
        """
        # Format timestamps to ISO format with Z timezone indicator
        formatted_alerts = []
        for alert in self.alerts:
            # Parse the original timestamp
            try:
                dt = datetime.strptime(alert['timestamp'], '%Y%m%d %H:%M:%S.%f')
            except ValueError:
                dt = datetime.strptime(alert['timestamp'], '%Y%m%d %H:%M:%S')
            
            # Create a new alert with formatted timestamp
            formatted_alert = {
                'satelliteId': alert['satelliteId'],
                'severity': alert['severity'],
                'component': alert['component'],
                'timestamp': dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            }
            formatted_alerts.append(formatted_alert)
        
        return json.dumps(formatted_alerts, indent=4)

def main():
    """
    Main function to execute the monitoring application.
    """
    import sys
    
    # Check for input file argument
    if len(sys.argv) != 2:
        print("Usage: python satellite_monitor.py <input_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Create monitor and process file
    monitor = SatelliteMonitor()
    monitor.process_file(input_file)
    
    # Output alerts as JSON
    print(monitor.get_alerts())

if __name__ == "__main__":
    main()
