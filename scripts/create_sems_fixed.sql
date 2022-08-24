CREATE VIEW public.sems_total_min AS
 SELECT min(sems.yield_total) AS yield_total_min,
    date(sems.sample) AS date
   FROM public.sems
  GROUP BY (date(sems.sample));


CREATE VIEW public.sems_fixed AS
 SELECT (s.yield_total - stm.yield_total_min) AS yield_today,
    s.yield_today AS yield_today_broken,
    s.sample,
    s.current_dc_1,
    s.current_dc_2,
    s.voltage_dc_1,
    s.voltage_dc_2,
    s.power_dc_1,
    s.power_dc_2,
    s.current_ac_1,
    s.current_ac_2,
    s.current_ac_3,
    s.voltage_ac_1,
    s.voltage_ac_2,
    s.voltage_ac_3,
    s.power_ac,
    s.yield_total,
    s.net_frequency_1,
    s.net_frequency_2,
    s.net_frequency_3,
    s.temperature
   FROM (public.sems s
     JOIN public.sems_total_min stm ON ((stm.date = date(s.sample))));


