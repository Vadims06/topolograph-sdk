"""Event resource for Topolograph API."""

from typing import Optional, List, Dict, Any
from datetime import datetime


class Event:
    """Represents a topology event."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize an Event object.
        
        Args:
            data: Event data from API
        """
        self.event_detected_by = data.get('event_detected_by')
        self.graph_time = data.get('graph_time')
        self.timestamp = data.get('timestamp')
        self.watcher_time = data.get('watcher_time')
        self.event_status = data.get('event_status')
        self.watcher_name = data.get('watcher_name')
        self.level_number = data.get('level_number')
        self.event_name = data.get('event_name')
        self.event_object = data.get('event_object')
        self.area_num = data.get('area_num')
        self.asn = data.get('asn')
        self.new_cost = data.get('new_cost')
        self.old_cost = data.get('old_cost')
        self.protocol = data.get('protocol')
        self.local_ip_address = data.get('local_ip_address')
        self.object_status = data.get('object_status')
        # Network-specific fields
        self.subnet_type = data.get('subnet_type')
        self.int_ext_subtype = data.get('int_ext_subtype')
        # Additional attributes
        self.attributes = {k: v for k, v in data.items() if not hasattr(self, k)}
    
    def __repr__(self) -> str:
        return f"Event(name={self.event_name}, status={self.event_status}, object={self.event_object})"


class EventsManager:
    """Manager for event resources."""
    
    def __init__(self, client, graph_time: str):
        """Initialize the EventsManager.
        
        Args:
            client: Topolograph client instance
            graph_time: Graph time identifier
        """
        self._client = client
        self.graph_time = graph_time
    
    def get_network_events(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        last_minutes: Optional[int] = None
    ) -> Dict[str, List[Event]]:
        """Get network events (network up/down and network cost changes).
        
        Args:
            start_time: Start time in ISO format (e.g., "2025-06-30T20:00:00Z")
            end_time: End time in ISO format
            last_minutes: Number of minutes to look back (overrides start_time/end_time)
        
        Returns:
            Dictionary with keys:
            - network_up_down_events: List of network up/down events
            - network_cost_change_events: List of network cost change events
        """
        params = {}
        if last_minutes:
            params['last_minutes'] = last_minutes
        else:
            if start_time:
                params['start_time'] = start_time
            if end_time:
                params['end_time'] = end_time
        
        response = self._client.get(
            f'/events/{self.graph_time}/networks',
            params=params
        )
        events_data = response.json()
        
        result = {
            'network_up_down_events': [],
            'network_cost_change_events': []
        }
        
        if 'network_up_down_events' in events_data:
            result['network_up_down_events'] = [
                Event(e) for e in events_data['network_up_down_events']
            ]
        
        if 'network_cost_change_events' in events_data:
            result['network_cost_change_events'] = [
                Event(e) for e in events_data['network_cost_change_events']
            ]
        
        return result
    
    def get_adjacency_events(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        last_minutes: Optional[int] = None
    ) -> Dict[str, List[Event]]:
        """Get adjacency events (host up/down and link cost changes).
        
        Args:
            start_time: Start time in ISO format (e.g., "2025-06-30T20:00:00Z")
            end_time: End time in ISO format
            last_minutes: Number of minutes to look back (overrides start_time/end_time)
        
        Returns:
            Dictionary with keys:
            - all_host_up_down_events: List of all host up/down events
            - single_host_up_events: List of host up events
            - single_host_down_events: List of host down events
            - adjacency_cost_change_events: List of link cost change events
        """
        params = {}
        if last_minutes:
            params['last_minutes'] = last_minutes
        else:
            if start_time:
                params['start_time'] = start_time
            if end_time:
                params['end_time'] = end_time
        
        response = self._client.get(
            f'/events/{self.graph_time}/adjacency',
            params=params
        )
        events_data = response.json()
        
        result = {
            'all_host_up_down_events': [],
            'single_host_up_events': [],
            'single_host_down_events': [],
            'adjacency_cost_change_events': []
        }
        
        if 'all_host_up_down_events' in events_data:
            result['all_host_up_down_events'] = [
                Event(e) for e in events_data['all_host_up_down_events']
            ]
        
        if 'single_host_up_events' in events_data:
            result['single_host_up_events'] = [
                Event(e) for e in events_data['single_host_up_events']
            ]
        
        if 'single_host_down_events' in events_data:
            result['single_host_down_events'] = [
                Event(e) for e in events_data['single_host_down_events']
            ]
        
        if 'adjacency_cost_change_events' in events_data:
            result['adjacency_cost_change_events'] = [
                Event(e) for e in events_data['adjacency_cost_change_events']
            ]
        
        return result
