"""
Tests for setting up an EventsLoader and a BlazeEventsLoader.
"""
from nose_parameterized import parameterized

import blaze as bz
import pandas as pd
from pandas.util.testing import assert_series_equal, TestCase

from zipline.pipeline.common import (
    ANNOUNCEMENT_FIELD_NAME,
    SID_FIELD_NAME,
    TS_FIELD_NAME
)
from zipline.pipeline.data import DataSet, Column
from zipline.pipeline.loaders.blaze.events import BlazeEventsLoader
from zipline.pipeline.loaders.events import (
    BAD_DATA_FORMAT_ERROR,
    DF_NO_TS_NOT_INFER_TS_ERROR,
    DTINDEX_NOT_INFER_TS_ERROR,
    EventsLoader,
    SERIES_NO_DTINDEX_ERROR,
    WRONG_COLS_ERROR,
)
from zipline.utils.memoize import lazyval
from zipline.utils.numpy_utils import datetime64ns_dtype

ABSTRACT_METHODS_ERROR = 'abstract methods concrete_loader'


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


class EventDataSetLoaderNoExpectedCols(EventsLoader):

    def __init__(self,
                 all_dates,
                 events_by_sid,
                 infer_timestamps=False,
                 dataset=EventDataSet):
        super(EventDataSetLoaderNoExpectedCols, self).__init__(
            all_dates,
            events_by_sid,
            infer_timestamps=infer_timestamps,
            dataset=dataset,
        )


dtx = pd.date_range('2014-01-01', '2014-01-10')


def assert_loader_error(events_by_sid, error, msg, infer_timestamps):
    with TestCase.assertRaises(error) as context:
        EventDataSetLoader(
            dtx, events_by_sid, infer_timestamps=infer_timestamps,
        )
        TestCase.assertTrue(msg in context.exception)


class EventLoaderTestCase(TestCase):

    def test_no_expected_cols_defined(self):
        events_by_sid = {0: pd.DataFrame({ANNOUNCEMENT_FIELD_NAME: dtx})}
        assert_loader_error(events_by_sid, TypeError, ABSTRACT_METHODS_ERROR,
                            True)

    def test_wrong_cols(self):
        wrong_col_name = 'some_other_col'
        # Test wrong cols (cols != expected)
        events_by_sid = {0: pd.DataFrame({wrong_col_name: dtx})}
        assert_loader_error(
            events_by_sid, ValueError, WRONG_COLS_ERROR.format(
                expected_columns=EventDataSetLoader.expected_cols,
                sid=0,
                resulting_columns=wrong_col_name,
            ),
            True
        )

    @parameterized.expand([
        # DataFrame without timestamp column and infer_timestamps = True
        [pd.DataFrame({ANNOUNCEMENT_FIELD_NAME: dtx}), True],
        # DataFrame with timestamp column
        [pd.DataFrame({ANNOUNCEMENT_FIELD_NAME: dtx,
                       TS_FIELD_NAME: dtx}), False],
        # DatetimeIndex with infer_timestamps = True
        [pd.DatetimeIndex(dtx, name=ANNOUNCEMENT_FIELD_NAME), True],
        # Series with DatetimeIndex as index and infer_timestamps = False
        [pd.Series(dtx, index=dtx, name=ANNOUNCEMENT_FIELD_NAME), False]
    ])
    def test_conversion_to_df(self, df, infer_timestamps):

        events_by_sid = {0: df}
        loader = EventDataSetLoader(
            dtx,
            events_by_sid,
            infer_timestamps=infer_timestamps,
        )
        self.assertEqual(
            loader.events_by_sid.keys(),
            events_by_sid.keys(),
        )

        if infer_timestamps:
            expected = pd.Series(index=[dtx[0]] * 10, data=dtx,
                                 name=ANNOUNCEMENT_FIELD_NAME)
        else:
            expected = pd.Series(index=dtx, data=dtx,
                                 name=ANNOUNCEMENT_FIELD_NAME)
            expected.index.name = TS_FIELD_NAME
        # Check that index by first given date has been added
        assert_series_equal(
            loader.events_by_sid[0][ANNOUNCEMENT_FIELD_NAME],
            expected,
        )

    @parameterized.expand([
        # DataFrame without timestamp column and infer_timestamps = True
        [pd.DataFrame({ANNOUNCEMENT_FIELD_NAME: dtx}),
         False,
         DF_NO_TS_NOT_INFER_TS_ERROR.format(
             timestamp_column_name=TS_FIELD_NAME,
             sid=0
         )
         ],
        # DatetimeIndex with infer_timestamps = False
        [pd.DatetimeIndex(dtx, name=ANNOUNCEMENT_FIELD_NAME), False,
         DTINDEX_NOT_INFER_TS_ERROR.format(sid=0)],
        # Series with DatetimeIndex as index and infer_timestamps = False
        [pd.Series(dtx, name=ANNOUNCEMENT_FIELD_NAME), False,
         SERIES_NO_DTINDEX_ERROR.format(sid=0)],
        # Some other data structure that is not expected
        [dtx, False, BAD_DATA_FORMAT_ERROR.format(sid=0)],
        [dtx, True, BAD_DATA_FORMAT_ERROR.format(sid=0)]
    ])
    def test_bad_conversion_to_df(self, df, infer_timestamps, msg):
        events_by_sid = {0: df}
        assert_loader_error(events_by_sid, ValueError, msg,
                            infer_timestamps=infer_timestamps)


class BlazeEventDataSetLoaderNoConcreteLoader(BlazeEventsLoader):
    def __init__(self,
                 expr,
                 dataset=EventDataSet,
                 **kwargs):
        super(
            BlazeEventDataSetLoaderNoConcreteLoader, self
        ).__init__(expr,
                   dataset=dataset,
                   **kwargs)


class BlazeEventLoaderTestCase(TestCase):
    # Blaze loader: need to test failure if no concrete loader
    def test_no_concrete_loader_defined(self):
        with TestCase.assertRaises(TypeError) as context:
            BlazeEventDataSetLoaderNoConcreteLoader(
                bz.Data(
                    pd.DataFrame({ANNOUNCEMENT_FIELD_NAME: dtx,
                                  SID_FIELD_NAME: 0
                                  })
                )
            )
            TestCase.assertTrue(ABSTRACT_METHODS_ERROR in context.exception)
