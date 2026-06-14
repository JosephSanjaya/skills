import msgspec

# 1. Defining struct with gc=False to bypass garbage collector tracking
class EventData(msgspec.Struct, gc=False):
    event_id: str
    name: str
    metadata: dict[str, str]

# 2. Re-usable Encoder and Decoder instances
json_decoder = msgspec.json.Decoder(list[EventData])
json_encoder = msgspec.json.Encoder()

def parse_events(raw_json: bytes) -> list[EventData]:
    """Extremely fast, low-overhead parsing of a list of events."""
    return json_decoder.decode(raw_json)

def serialize_events(events: list[EventData]) -> bytes:
    """Fast serialization to JSON bytes."""
    return json_encoder.encode(events)

if __name__ == "__main__":
    raw = b'[{"event_id":"123","name":"click","metadata":{"element":"btn_submit"}}]'
    events = parse_events(raw)
    print("Parsed Struct:", events)
    print("Serialized JSON:", serialize_events(events))
