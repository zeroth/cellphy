
class TrackPair:
    def __init__(self, track_a, track_b, time):
        self.tracks = {f'{track_a.suffix}': track_a, f'{track_b.suffix}': track_b}

        self.track_a = track_a
        self.track_b = track_b
        self.time = time
        self.name = f'{track_a.track_id}{track_a.suffix}-{track_b.track_id}{track_b.suffix}'
