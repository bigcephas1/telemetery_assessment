# telemetery_assessment


Satellite Telemetry Monitoring System - Step-by-Step Documentation
Problem Understanding

    Mission Context Analysis:

        Identified the system monitors two satellites tracking Earth's magnetic fields

        Recognized critical components: thermostats (TSTAT) and batteries (BATT)

        Understood the tandem orbit configuration requiring continuous monitoring

    Requirements Clarification:

        Extracted two main alert conditions:

            3 battery voltage readings below red low limit within 5 minutes

            3 thermostat readings above red high limit within 5 minutes

        Noted input format: pipe-delimited ASCII text files

        Defined output format: JSON with specific fields

Solution Design

    Architecture Planning:

        Chose object-oriented approach with a SatelliteMonitor class

        Designed data structures:

            readings: defaultdict to store recent telemetry by satellite/component

            alerts: list to accumulate violation alerts

        Established 5-minute time window as timedelta

    Data Flow Design:

        File → Line Parser → Telemetry Processor → Violation Checker → Alert Generator

        Ensured chronological processing while maintaining state

Implementation Steps

    Core Components Implementation:

5.1 Data Ingestion Layer
python

def parse_line(self, line):
    """Step 5.1.1: Parse raw telemetry line into structured data"""
    fields = line.strip().split('|')
    return {
        'timestamp': fields[0],  # Preserve original string
        'satelliteId': int(fields[1]),
        'limits': {
            'red_high': float(fields[2]),
            'yellow_high': float(fields[3]),
            'yellow_low': float(fields[4]),
            'red_low': float(fields[5])
        },
        'raw_value': float(fields[6]),
        'component': fields[7]
    }

5.2 Telemetry Processing
python

def process_telemetry(self, data):
    """Step 5.2.1: Convert and store telemetry data"""
    # Step 5.2.2: Handle timestamp conversion
    try:
        dt = datetime.strptime(data['timestamp'], '%Y%m%d %H:%M:%S.%f')
    except ValueError:
        dt = datetime.strptime(data['timestamp'], '%Y%m%d %H:%M:%S')
    
    # Step 5.2.3: Create storage key
    key = (data['satelliteId'], data['component'])
    
    # Step 5.2.4: Store reading with both datetime and original timestamp
    self.readings[key].append({
        'datetime': dt,
        'value': data['raw_value'],
        'limit': (data['limits']['red_high'] if data['component'] == 'TSTAT'
                 else data['limits']['red_low']),
        'original_ts': data['timestamp']
    })

5.3 Violation Detection
python

def check_violations(self, key):
    """Step 5.3.1: Implement sliding window violation detection"""
    sat_id, component = key
    readings = self.readings[key]
    
    # Step 5.3.2: Component-specific threshold check
    if component == 'TSTAT':
        violators = [r for r in readings if r['value'] > r['limit']]
        severity = 'RED HIGH'
    elif component == 'BATT':
        violators = [r for r in readings if r['value'] < r['limit']]
        severity = 'RED LOW'
    else:
        return
    
    # Step 5.3.3: Three-reading window check
    if len(violators) >= 3:
        violators.sort(key=lambda x: x['datetime'])
        
        # Step 5.3.4: Sliding window implementation
        for i in range(len(violators) - 2):
            if (violators[i+2]['datetime'] - violators[i]['datetime'] <= 
                self.time_window):
                alert = {
                    'satelliteId': sat_id,
                    'severity': severity,
                    'component': component,
                    'timestamp': violators[i]['original_ts']
                }
                if alert not in self.alerts:
                    self.alerts.append(alert)
                break

5.4 Alert Generation
python

def get_alerts(self):
    """Step 5.4.1: Format alerts to specification"""
    formatted = []
    for alert in self.alerts:
        # Step 5.4.2: ISO 8601 timestamp conversion
        try:
            dt = datetime.strptime(alert['timestamp'], '%Y%m%d %H:%M:%S.%f')
        except ValueError:
            dt = datetime.strptime(alert['timestamp'], '%Y%m%d %H:%M:%S')
        
        # Step 5.4.3: Millisecond precision handling
        iso_ts = dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        
        formatted.append({
            **alert,
            'timestamp': iso_ts
        })
    
    # Step 5.4.4: JSON serialization
    return json.dumps(formatted, indent=4)

Validation Approach

    Testing Strategy:

        Unit tests for each component:

            Line parsing with various timestamp formats

            Violation detection logic

            Edge cases (exactly 5 minute intervals)

        Integration test with sample input

        Output format validation against requirements

    Sample Data Verification:

        Confirmed alert for satellite 1000 TSTAT (3 high readings)

        Verified battery alert timing constraints

        Checked JSON output formatting

Optimization Considerations

    Performance Enhancements:

        Time-ordered processing eliminates need for full sorting

        Early termination in violation checks

        Dictionary-based storage for O(1) access

    Maintainability Features:

        Clear separation of concerns

        Documented data structures

        Component-based violation detection

Final Implementation

    Complete System Integration:

        Wrapped in command-line executable

        Added proper error handling for file operations

        Ensured clean JSON output formatting

python

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python monitor.py <telemetry_file>")
        sys.exit(1)
    
    monitor = SatelliteMonitor()
    monitor.process_file(sys.argv[1])
    print(monitor.get_alerts())

