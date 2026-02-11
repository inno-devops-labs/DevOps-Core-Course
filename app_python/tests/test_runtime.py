from datetime import datetime
from core.runtime import set_start_time, get_uptime
import core.runtime


def test_set_start_time():
    set_start_time()
    assert core.runtime.START_TIME is not None
    assert isinstance(core.runtime.START_TIME, datetime)


def test_get_uptime_success():
    set_start_time()
    uptime = get_uptime()
    
    assert "seconds" in uptime
    assert "human" in uptime
    assert isinstance(uptime["seconds"], int)
    assert isinstance(uptime["human"], str)
    assert uptime["seconds"] >= 0
    assert "hours" in uptime["human"]
    assert "minutes" in uptime["human"]


def test_get_uptime_increases():
    set_start_time()
    import time
    
    uptime1 = get_uptime()
    time.sleep(1)
    uptime2 = get_uptime()
    
    assert uptime2["seconds"] >= uptime1["seconds"]
