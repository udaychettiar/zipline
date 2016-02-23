#
# Copyright 2016 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from cpython cimport bool

cdef class BarData:
    cdef object data_portal
    cdef object simulation_dt_func
    cdef object data_frequency
    cdef dict _views
    cdef object _get_equity_price_view(BarData, object)
    cdef object _create_sid_view(BarData, object)
    cdef bool _is_stale_for_asset(BarData, object, object, object)
    cdef bool _can_trade_for_asset(BarData, object, object, object)
    cdef object _calculate_universe(BarData)
    cdef object _universe_func
    cdef object _universe_last_updated_at
    cdef object _last_calculated_universe


cdef class SidView:
    cdef object asset
    cdef object data_portal
    cdef object simulation_dt_func
    cdef object data_frequency
