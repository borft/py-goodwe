
CREATE TABLE public.electricity (
    sample timestamp without time zone NOT NULL,
    kwh_in_1 numeric(9,3),
    kwh_in_2 numeric(9,3),
    kwh_out_1 numeric(9,3),
    kwh_out_2 numeric(9,3),
    power_in numeric(5,3),
    power_out numeric(5,3),
    current_l1 smallint,
    current_l2 smallint,
    current_l3 smallint,
    power_in_l1 numeric(5,3),
    power_in_l2 numeric(5,3),
    power_in_l3 numeric(5,3),
    power_out_l1 numeric(5,3),
    power_out_l2 numeric(5,3),
    power_out_l3 numeric(5,3),
    voltage_l1 numeric(6,3),
    voltage_l2 numeric(6,3),
    voltage_l3 numeric(6,3)
);


CREATE TABLE public.sems (
    sample timestamp without time zone NOT NULL,
    current_dc_1 numeric(4,1) DEFAULT 0,
    current_dc_2 numeric(4,1) DEFAULT 0,
    voltage_dc_1 numeric(4,1) DEFAULT 0,
    voltage_dc_2 numeric(4,1) DEFAULT 0,
    power_dc_1 smallint DEFAULT 0,
    power_dc_2 smallint DEFAULT 0,
    current_ac_1 numeric(4,1) DEFAULT 0,
    current_ac_2 numeric(4,1) DEFAULT 0,
    current_ac_3 numeric(4,1) DEFAULT 0,
    voltage_ac_1 numeric(4,1) DEFAULT 0,
    voltage_ac_2 numeric(4,1) DEFAULT 0,
    voltage_ac_3 numeric(4,1) DEFAULT 0,
    power_ac smallint DEFAULT 0,
    yield_today numeric(4,1) DEFAULT 0,
    yield_total numeric(6,1) DEFAULT 0,
    net_frequency_1 numeric(4,2) DEFAULT 0,
    net_frequency_2 numeric(4,2) DEFAULT 0,
    net_frequency_3 numeric(4,2) DEFAULT 0,
    temperature numeric(4,2) DEFAULT 0
);



ALTER TABLE ONLY public.electricity
    ADD CONSTRAINT electricity_pkey PRIMARY KEY (sample);



ALTER TABLE ONLY public.sems
    ADD CONSTRAINT sems_pkey PRIMARY KEY (sample);

