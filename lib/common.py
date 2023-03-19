def duration2time(duration):
    seconds = duration % (24 * 3600) 
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    if hour > 0:
        time = '%dh %02dm %02ds' % (hour, minutes, seconds)
    else:
        time = '%02dm %02ds' % (minutes, seconds)

    return time