import yaml
import schedule
import time

class YamlScheduler(object):
    """YamlScheduler: Singleton for in process scheduling
    Reads schedule.yml containing:
    
    List of weekdays that define a start-end window to run the task for at a desired interval
    Days need not be unique

        weekdays:
        - weekday:
            name: "tuesday"
            start: "21:00"
            end: "22:00"
            minutes: 5

    Interval period in YAML can be specified as seconds, minutes or hours
    """    
    _instance = None
    __stopwaiting = False
    __logger = None
    __runOnce = False

    def __new__(cls):
        """Singleton initialisation. Not much to see here. Move along. Move along.

        """        
        if cls._instance is None:            
            cls._instance = super(YamlScheduler, cls).__new__(cls)
            # Put any initialization here.
            cls.__stopwaiting = False
            cls.__runOnce = False
        return cls._instance

    @classmethod
    def Wait(self):
        """Wait: blocks main execution thread waiting for next job.
        Might be an idea to set some jobs scheduled first.
        """        
        while not self.__stopwaiting:
            schedule.run_pending()
            time.sleep(1)
    
    @classmethod 
    def RunOnce(cls, value):
        """"RunOnce: Only run one window - use for testing

        Args:
            value (bool) : True - run only one schedule window
        """
        cls.__runOnce = value

    @classmethod 
    def IsRunOnce(cls):
        return cls.__runOnce

    @classmethod
    def Stop(cls):
        """Stop: Stop the main execution loop.
        Allows the 
        Something altogether more sophisticated required for multithreading
        """        
        cls.__stopwaiting = True

    @classmethod
    def __StartWindow(self, job, jobArgs, interval, intervalUnit, tag):
        """__StartWindow: Internal method that starts a window that the job will run in.
        Called by the scheduler at the start of the window.

        Args:
            job (fn)       : The python function to call
            interval (int) : How frequently to call the job during the time window. Seconds for development, minutes for final
            tag (string)   : What to tag this job with. Used to cancel the job at the end of the window
                             format is s_[weekday name]_hh:mm_hh:mm
        """

        if not self.__logger is None:
            self.__logger.info('Scheduling ' + job.__name__ + ' as ' + tag + ' every ' + str(interval) + ' ' + intervalUnit + '...')

        # Call the job right at the start of the window as the scheduler will wait interval units before firing for the first time
        job(jobArgs)
        getattr(schedule.every(interval), intervalUnit).do(job, jobArgs).tag(tag)

    @classmethod
    def __StopWindow(self, tag):
        """__StopWindow: Internal method that finished a window that the job will run in.
        Called by the scheduler at the end of the window.

        Args:
            tag (string)   : The job tag to cancel. 
                             format is s_[weekday name]_hh:mm_hh:mm
        """
        if not self.__logger is None:
            self.__logger.info('Unscheduling ' + tag + '...')

        if YamlScheduler.IsRunOnce():
            YamlScheduler.Stop()

        schedule.clear(tag)

    @classmethod
    def Initialise(self, logger, jobToSchedule, jobArguments, config="schedule.yml"):
        """Initialise: Set up the scheduled jobs from the YAML file.

        Args:
            logger (fn) : Python logging singleton, if not None
            jobToSchedule (fn) : The job to run
            jobArguments (object) : wrapper for arguments to pass to the job
        """
        try:
            self.__stopwaiting = False
            self.__logger = logger
            with open(config, 'r') as ymlfile:
                cfg = yaml.load(ymlfile, yaml.FullLoader)

                if not self.__logger is None:
                    self.__logger.info('Loaded config')

                weekdays = cfg['weekdays']
                if weekdays is not None:
                    for scheduleInstance in weekdays:
                        weekday = scheduleInstance['weekday']
                        dayname = weekday['name']
                        windowStart = weekday['start']
                        windowEnd = weekday['end']                        
                        jobTag = 's_' + dayname + '_' + windowStart + '_' + windowEnd
                        
                        # Get which interval is specified
                        intervalNames = ['seconds', 'minutes', 'hours']
                        intervalName = None
                        for iName in intervalNames:
                            if iName in weekday:
                                intervalName = iName
                        
                        # Now we know the interval get its value
                        if intervalName is None:
                            raise('Interval for schedule must be given as seconds, minutes or hours')
                        intervalValue = int(weekday[intervalName])

                        # Schedule the start and end window on the specific day
                        # Call schedule.every().<<dayname>>.at(...
                        if not self.__logger is None:
                            self.__logger.info('Scheduling window for ' + dayname + ' at ' + windowStart + ' to ' + windowEnd)
                        getattr(schedule.every(), dayname).at(windowStart).do(YamlScheduler.__StartWindow, job=jobToSchedule, jobArgs=jobArguments, interval=intervalValue, intervalUnit=intervalName, tag=jobTag)
                        getattr(schedule.every(), dayname).at(windowEnd).do(YamlScheduler.__StopWindow, tag=jobTag)

        except Exception as e:
            if not self.__logger is None:
                self.__logger.critical('Failed (' + e + ')')
