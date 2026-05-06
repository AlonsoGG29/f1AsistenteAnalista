from sqlalchemy import (
    Column, Integer, String, Float, Date, Time,
    ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class Season(Base):
    __tablename__ = "seasons"
    year = Column(Integer, primary_key=True)
    url = Column(String(255))
    races = relationship("Race", back_populates="season")


class Circuit(Base):
    __tablename__ = "circuits"
    circuitId = Column(Integer, primary_key=True, autoincrement=True, name="circuitid")
    circuitRef = Column(String(255), nullable=False, name="circuitref")
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    country = Column(String(255))
    lat = Column(Float)
    lng = Column(Float)
    alt = Column(Integer)
    url = Column(String(255))
    races = relationship("Race", back_populates="circuit")


class Driver(Base):
    __tablename__ = "drivers"
    driverId = Column(Integer, primary_key=True, autoincrement=True, name="driverid")
    driverRef = Column(String(255), nullable=False, name="driverref")
    number = Column(Integer)
    code = Column(String(3))
    forename = Column(String(255), nullable=False)
    surname = Column(String(255), nullable=False)
    dob = Column(Date)
    nationality = Column(String(255))
    url = Column(String(255))
    results = relationship("Result", back_populates="driver")
    standings = relationship("DriverStanding", back_populates="driver")


class Constructor(Base):
    __tablename__ = "constructors"
    constructorId = Column(Integer, primary_key=True, autoincrement=True, name="constructorid")
    constructorRef = Column(String(255), nullable=False, name="constructorref")
    name = Column(String(255), unique=True, nullable=False)
    nationality = Column(String(255))
    url = Column(String(255))
    results = relationship("Result", back_populates="constructor")
    standings = relationship("ConstructorStanding", back_populates="constructor")


class Status(Base):
    __tablename__ = "status"
    statusId = Column(Integer, primary_key=True, autoincrement=True, name="statusid")
    status = Column(String(255), nullable=False)


class Race(Base):
    __tablename__ = "races"
    raceId = Column(Integer, primary_key=True, autoincrement=True, name="raceid")
    year = Column(Integer, ForeignKey("seasons.year"))
    round = Column(Integer, nullable=False)
    circuitId = Column(Integer, ForeignKey("circuits.circuitid"), name="circuitid")
    name = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time)
    url = Column(String(255))
    fp1_date = Column(Date, name="fp1_date")
    fp1_time = Column(Time, name="fp1_time")
    fp2_date = Column(Date, name="fp2_date")
    fp2_time = Column(Time, name="fp2_time")
    fp3_date = Column(Date, name="fp3_date")
    fp3_time = Column(Time, name="fp3_time")
    quali_date = Column(Date, name="quali_date")
    quali_time = Column(Time, name="quali_time")
    sprint_date = Column(Date, name="sprint_date")
    sprint_time = Column(Time, name="sprint_time")

    season = relationship("Season", back_populates="races")
    circuit = relationship("Circuit", back_populates="races")
    results = relationship("Result", back_populates="race")
    pit_stops = relationship("PitStop", back_populates="race")
    lap_times = relationship("LapTime", back_populates="race")
    driver_standings = relationship("DriverStanding", back_populates="race")
    constructor_standings = relationship("ConstructorStanding", back_populates="race")


class Result(Base):
    __tablename__ = "results"
    resultId = Column(Integer, primary_key=True, autoincrement=True, name="resultid")
    raceId = Column(Integer, ForeignKey("races.raceid"), name="raceid")
    driverId = Column(Integer, ForeignKey("drivers.driverid"), name="driverid")
    constructorId = Column(Integer, ForeignKey("constructors.constructorid"), name="constructorid")
    number = Column(Integer)
    grid = Column(Integer)
    position = Column(Integer)
    positionText = Column(String(255), nullable=False, name="positiontext")
    positionOrder = Column(Integer, nullable=False, name="positionorder")
    points = Column(Float, nullable=False)
    laps = Column(Integer, nullable=False)
    time = Column(String(255))
    milliseconds = Column(Integer)
    fastestLap = Column(Integer, name="fastestlap")
    rank = Column(Integer)
    fastestLapTime = Column(String(255), name="fastestlaptime")
    fastestLapSpeed = Column(String(255), name="fastestlapspeed")
    statusId = Column(Integer, ForeignKey("status.statusid"), name="statusid")

    race = relationship("Race", back_populates="results")
    driver = relationship("Driver", back_populates="results")
    constructor = relationship("Constructor", back_populates="results")
    status = relationship("Status")


class PitStop(Base):
    __tablename__ = "pit_stops"
    raceId = Column(Integer, ForeignKey("races.raceid"), primary_key=True, name="raceid")
    driverId = Column(Integer, ForeignKey("drivers.driverid"), primary_key=True, name="driverid")
    stop = Column(Integer, primary_key=True, nullable=False)
    lap = Column(Integer, nullable=False)
    time = Column(Time, nullable=False)
    duration = Column(String(255))
    milliseconds = Column(Integer)

    race = relationship("Race", back_populates="pit_stops")
    driver = relationship("Driver")


class LapTime(Base):
    __tablename__ = "lap_times"
    raceId = Column(Integer, ForeignKey("races.raceid"), primary_key=True, name="raceid")
    driverId = Column(Integer, ForeignKey("drivers.driverid"), primary_key=True, name="driverid")
    lap = Column(Integer, primary_key=True, nullable=False)
    position = Column(Integer)
    time = Column(String(255))
    milliseconds = Column(Integer)

    race = relationship("Race", back_populates="lap_times")
    driver = relationship("Driver")


class DriverStanding(Base):
    __tablename__ = "driver_standings"
    driverStandingsId = Column(Integer, primary_key=True, autoincrement=True, name="driverstandingsid")
    raceId = Column(Integer, ForeignKey("races.raceid"), name="raceid")
    driverId = Column(Integer, ForeignKey("drivers.driverid"), name="driverid")
    points = Column(Float, nullable=False, default=0)
    position = Column(Integer)
    positionText = Column(String(255), name="positiontext")
    wins = Column(Integer, nullable=False, default=0)

    race = relationship("Race", back_populates="driver_standings")
    driver = relationship("Driver", back_populates="standings")


class ConstructorStanding(Base):
    __tablename__ = "constructor_standings"
    constructorStandingsId = Column(Integer, primary_key=True, autoincrement=True, name="constructorstandingsid")
    raceId = Column(Integer, ForeignKey("races.raceid"), name="raceid")
    constructorId = Column(Integer, ForeignKey("constructors.constructorid"), name="constructorid")
    points = Column(Float, nullable=False, default=0)
    position = Column(Integer)
    positionText = Column(String(255), name="positiontext")
    wins = Column(Integer, nullable=False, default=0)

    race = relationship("Race", back_populates="constructor_standings")
    constructor = relationship("Constructor", back_populates="standings")
