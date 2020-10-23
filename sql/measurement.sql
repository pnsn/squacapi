--
-- PostgreSQL database dump
--

-- Dumped from database version 12.4
-- Dumped by pg_dump version 12.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: measurement_measurement; Type: TABLE; Schema: public; Owner: deploy
--

CREATE TABLE public.measurement_measurement (
    id SERIAL NOT NULL,
    created_at timestamp with time zone NOT NULL,
    value double precision NOT NULL,
    starttime timestamp with time zone NOT NULL,
    endtime timestamp with time zone NOT NULL,
    channel_id integer NOT NULL,
    metric_id integer NOT NULL,
    user_id integer NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    PRIMARY KEY(id, starttime)
) PARTITION BY RANGE(starttime); ---added by jc


ALTER TABLE public.measurement_measurement OWNER TO deploy;

--
-- Name: measurement_measurement_id_seq; Type: SEQUENCE; Schema: public; Owner: deploy
--



ALTER TABLE public.measurement_measurement_id_seq OWNER TO deploy;

-- --
-- -- Name: measurement_measurement_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: deploy
-- --

ALTER SEQUENCE public.measurement_measurement_id_seq OWNED BY public.measurement_measurement.id;


-- --
-- -- Name: measurement_measurement id; Type: DEFAULT; Schema: public; Owner: deploy
-- --

ALTER TABLE ONLY public.measurement_measurement ALTER COLUMN id SET DEFAULT nextval('public.measurement_measurement_id_seq'::regclass);


--
-- Name: measurement_measurement measurement_measurement_pkey; Type: CONSTRAINT; Schema: public; Owner: deploy
--

-- ALTER TABLE ONLY public.measurement_measurement
--     ADD CONSTRAINT measurement_measurement_pkey PRIMARY KEY (id);



-- Name: measurement_measurement_channel_id_38da7999; Type: INDEX; Schema: public; Owner: deploy
--

CREATE INDEX measurement_measurement_channel_id_38da7999 ON public.measurement_measurement USING btree (channel_id);


--
-- Name: measurement_measurement_metric_id_b3ffd686; Type: INDEX; Schema: public; Owner: deploy
--

CREATE INDEX measurement_measurement_metric_id_b3ffd686 ON public.measurement_measurement USING btree (metric_id);


--
-- Name: measurement_measurement_user_id_df2a9b1d; Type: INDEX; Schema: public; Owner: deploy
--

CREATE INDEX measurement_measurement_user_id_df2a9b1d ON public.measurement_measurement USING btree (user_id);


--
-- Name: measurement_startti_7d7fa1_idx; Type: INDEX; Schema: public; Owner: deploy
--

CREATE INDEX measurement_startti_7d7fa1_idx ON public.measurement_measurement USING btree (starttime DESC);



--
-- Name: measurement_measurement measurement_measurem_metric_id_b3ffd686_fk_measureme; Type: FK CONSTRAINT; Schema: public; Owner: deploy
--

ALTER TABLE public.measurement_measurement
    ADD CONSTRAINT measurement_measurem_metric_id_b3ffd686_fk_measureme FOREIGN KEY (metric_id) REFERENCES public.measurement_metric(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: measurement_measurement measurement_measurement_channel_id_38da7999_fk_nslc_channel_id; Type: FK CONSTRAINT; Schema: public; Owner: deploy
--

ALTER TABLE public.measurement_measurement
    ADD CONSTRAINT measurement_measurement_channel_id_38da7999_fk_nslc_channel_id FOREIGN KEY (channel_id) REFERENCES public.nslc_channel(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: measurement_measurement measurement_measurement_user_id_df2a9b1d_fk_core_user_id; Type: FK CONSTRAINT; Schema: public; Owner: deploy
--

ALTER TABLE  public.measurement_measurement
    ADD CONSTRAINT measurement_measurement_user_id_df2a9b1d_fk_core_user_id FOREIGN KEY (user_id) REFERENCES public.core_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- PostgreSQL database dump complete
--

