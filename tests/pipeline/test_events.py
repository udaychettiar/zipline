from functools import partial
from nose_parameterized import parameterized
import pandas as pd
import numpy as np
from pandas.util.testing import assert_series_equal, TestCase
from zipline.pipeline import SimplePipelineEngine, Pipeline
from zipline.pipeline.data import DataSet, Column
from zipline.pipeline.loaders.blaze.events import BlazeEventsCalendarLoader
from zipline.pipeline.loaders.events import EventsLoader, TS_FIELD_NAME
from zipline.utils.memoize import lazyval
from zipline.utils.numpy_utils import datetime64ns_dtype, NaTD, make_datetime64D
from zipline.utils.test_utils import make_simple_equity_info, gen_calendars, \
    num_days_in_range

DAYS_SINCE_PREV = 'days_since_prev'

PREVIOUS_ANNOUNCEMENT = 'previous_announcement'

ANNOUNCEMENT_FIELD_NAME = 'announcement_date'


class EventDataSet(DataSet):
    previous_announcement = Column(datetime64ns_dtype)


class EventDataSetLoader(EventsLoader):

    def __init__(self,
                 all_dates,
                 events_by_sid,
                 infer_timestamps=False,
                 dataset=EventDataSet):
        super(EventDataSetLoader, self).__init__(
            all_dates,
            events_by_sid,
            infer_timestamps=infer_timestamps,
            dataset=dataset,
        )

    @property
    def expected_cols(self):
        return frozenset([ANNOUNCEMENT_FIELD_NAME])

    @lazyval
    def previous_announcement_loader(self):
        return self._previous_event_date_loader(
            self.dataset.previous_announcement,
            ANNOUNCEMENT_FIELD_NAME,
        )

    @lazyval
    def next_announcement_loader(self):
        return self._previous_event_date_loader(
            self.dataset.previous_announcement,
            ANNOUNCEMENT_FIELD_NAME,
        )


class EventLoaderConversionTestCase(TestCase):

    def test_infer_timestamp(self):
        dtx = pd.date_range('2014-01-01', '2014-01-10')
        events_by_sid = {
            # No timestamp column - should index by first given date
            0: pd.DataFrame({ANNOUNCEMENT_FIELD_NAME: dtx}),
            # timestamp column exists - should index by it
            1: pd.DataFrame({ANNOUNCEMENT_FIELD_NAME: dtx, TS_FIELD_NAME: dtx})
        }
        loader = EventDataSetLoader(
            dtx,
            events_by_sid,
            infer_timestamps=True,
        )
        self.assertEqual(
            loader.events_by_sid.keys(),
            events_by_sid.keys(),
        )

        # Check that index by first given date has been added
        assert_series_equal(
            loader.events_by_sid[0][ANNOUNCEMENT_FIELD_NAME],
            pd.Series(index=[dtx[0]] * 10,
                      data=dtx,
                      name=ANNOUNCEMENT_FIELD_NAME),
        )

        # Check that timestamp column was turned into index
        modified_events_by_sid_date_col = pd.Series(data=np.array(
            events_by_sid[1][ANNOUNCEMENT_FIELD_NAME]),
            index=events_by_sid[1][TS_FIELD_NAME],
            name=ANNOUNCEMENT_FIELD_NAME)
        assert_series_equal(
            loader.events_by_sid[1][ANNOUNCEMENT_FIELD_NAME],
            modified_events_by_sid_date_col,
        )

