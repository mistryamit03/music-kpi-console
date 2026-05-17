-- ============================================================
-- Snowflake Setup Script
-- Project: Music KPI Console - Streaming and Campaign Analytics
-- Purpose: Create database, raw schema, and warehouse
-- ============================================================

-- 1. Create the main project database. The MUSIC_KPI database stores all project data.
CREATE DATABASE IF NOT EXISTS MUSIC_KPI;

-- 2. Create RAW schema for ingested source data. Creates the RAW schema inside the MUSIC_KPI database. The RAW schema stores ingested source data before transformation.

CREATE SCHEMA IF NOT EXISTS MUSIC_KPI.RAW;

-- 3. Create a small warehouse for loading and querying data
CREATE WAREHOUSE IF NOT EXISTS MUSIC_KPI_WH
    WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE;

-- Creates the compute warehouse used to run SQL queries and load data.

-- Explanation:

-- XSMALL keeps compute usage low.
-- AUTO_SUSPEND = 60 pauses the warehouse after 60 seconds of inactivity.
-- AUTO_RESUME = TRUE restarts the warehouse automatically when needed.
-- INITIALLY_SUSPENDED = TRUE creates the warehouse in a suspended state.



-- 4. Set active Snowflake context. Everytime when you start a new SQL file, you need to use this to activate it. These commands tell Snowflake which warehouse, database, and schema to use.

USE WAREHOUSE MUSIC_KPI_WH;
USE DATABASE MUSIC_KPI;
USE SCHEMA RAW;