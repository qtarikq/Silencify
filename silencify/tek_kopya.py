"""
Programın aynı anda yalnızca BİR kopyasının çalışmasını sağlar.

İki motor aynı anda çalışırsa ikisi de Spotify'ın sesini kısıp açmaya çalışır ve
birbirinin işine karışır. Windows'un "mutex" (aynı anda tek sahibi olabilen kilit)
özelliğini kullanırız: kilidi ilk alan çalışır, ikinci açılış kilidin dolu olduğunu görür.
Program kapanınca Windows kilidi kendiliğinden bırakır.
"""

import win32api
import win32event
import winerror

from surum import AD

KILIT_ADI = f"{AD}_TekKopya"
_kilit = None                   # Program açık kaldığı sürece kilit burada tutulur


def zaten_calisiyor_mu():
    """Programın başka bir kopyası çalışıyorsa True döndürür; değilse kilidi alır ve False döndürür."""
    global _kilit
    _kilit = win32event.CreateMutex(None, False, KILIT_ADI)
    return win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS
