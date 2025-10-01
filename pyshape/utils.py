from astropy.time import Time

#===Shape time formatting for mod/obs files
def time_shape2astropy(t: str) -> Time:
    parts = t.split()
    year, month, day, hour, minute, second = map(int, parts)
    iso_str = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
    return Time(iso_str, format='iso', scale='utc')

def time_astropy2shape(t: Time) -> str:
    dt = t.to_datetime()
    return f"{dt.year} {dt.month} {dt.day} {dt.hour} {dt.minute} {dt.second}"
