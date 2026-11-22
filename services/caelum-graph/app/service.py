"""
Neo4j Graph Service for caelum-graph microservice.
Handles all knowledge graph operations for human space exploration history.
"""

import os
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase, BoltDriver


class GraphService:
    """Service for interacting with Neo4j knowledge graph."""

    def __init__(self):
        """Initialize the graph service."""
        self._driver: Optional[BoltDriver] = None
        self._uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        self._user = os.getenv("NEO4J_USER", "neo4j")
        self._password = os.getenv("NEO4J_PASSWORD", "password")
    
    def _get_driver(self) -> BoltDriver:
        """Get or create the Neo4j driver instance."""
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                uri=self._uri,
                auth=(self._user, self._password)
            )
        return self._driver
    
    def verify_connection(self) -> bool:
        """Verify that the Neo4j connection is working."""
        try:
            with self._get_driver().session() as session:
                session.run("RETURN 1")
            return True
        except Exception:
            return False
    
    def seed_basic_subgraph(self) -> Dict[str, Any]:
        """Seed the Neo4j database with basic space exploration data."""
        cypher_query = """
        // Create organizations
        MERGE (nasa:Organization {name: 'NASA', country: 'United States', founded: 1958})
        MERGE (esa:Organization {name: 'ESA', country: 'Europe', founded: 1975})
        MERGE (spacex:Organization {name: 'SpaceX', country: 'United States', founded: 2002})
        MERGE (roscosmos:Organization {name: 'Roscosmos', country: 'Russia', founded: 1992})
        MERGE (jaxa:Organization {name: 'JAXA', country: 'Japan', founded: 2003})
        MERGE (cnsa:Organization {name: 'CNSA', country: 'China', founded: 1993})
        MERGE (soviets:Organization {name: 'Soviet Space Program', country: 'Soviet Union', founded: 1955, ended: 1991})
        MERGE (uaesa:Organization {name: 'UAESA', country: 'United Arab Emirates', founded: 2006})
        
        // Create celestial bodies
        MERGE (mars:CelestialBody {name: 'Mars', type: 'planet', discovered: 'Ancient'})
        MERGE (moon:CelestialBody {name: 'Moon', type: 'natural_satellite', discovered: 'Ancient'})
        MERGE (venus:CelestialBody {name: 'Venus', type: 'planet', discovered: 'Ancient'})
        MERGE (jupiter:CelestialBody {name: 'Jupiter', type: 'planet', discovered: 'Ancient'})
        MERGE (saturn:CelestialBody {name: 'Saturn', type: 'planet', discovered: 'Ancient'})
        MERGE (mercury:CelestialBody {name: 'Mercury', type: 'planet', discovered: 'Ancient'})
        MERGE (comet67p:CelestialBody {name: '67P/Churyumov-Gerasimenko', type: 'comet', discovered: '1969'})
        
        // Apollo 11 - Moon landing
        MERGE (apollo11:Mission {name: 'Apollo 11', launch_date: '1969-07-16', mission_type: 'crewed', status: 'success'})
        MERGE (apollo11)-[:LAUNCHED_BY]->(nasa)
        MERGE (apollo11)-[:TARGETED]->(moon)
        
        MERGE (eagle:Spacecraft {name: 'Eagle', type: 'lunar_module', mission: 'Apollo 11'})
        MERGE (apollo11)-[:USED_SPACECRAFT]->(eagle)
        
        MERGE (neil:Person {name: 'Neil Armstrong', role: 'astronaut', nationality: 'American', birth: 1930, death: 2012})
        MERGE (buzz:Person {name: 'Buzz Aldrin', role: 'astronaut', nationality: 'American', birth: 1930})
        MERGE (michael:Person {name: 'Michael Collins', role: 'astronaut', nationality: 'American', birth: 1930, death: 2021})
        
        MERGE (neil)-[:PARTICIPATED_IN]->(apollo11)
        MERGE (buzz)-[:PARTICIPATED_IN]->(apollo11)
        MERGE (michael)-[:PARTICIPATED_IN]->(apollo11)
        
        MERGE (first_steps:Event {name: 'First Moon Landing', date: '1969-07-20', type: 'landing'})
        MERGE (first_steps)-[:PART_OF]->(apollo11)
        MERGE (first_steps)-[:AT]->(moon)
        MERGE (neil)-[:PERFORMED]->(first_steps)
        MERGE (buzz)-[:PERFORMED]->(first_steps)
        
        // Luna 2 - First impact on Moon
        MERGE (luna2:Mission {name: 'Luna 2', launch_date: '1959-01-02', mission_type: 'uncrewed', status: 'success'})
        MERGE (luna2)-[:LAUNCHED_BY]->(soviets)
        MERGE (luna2)-[:TARGETED]->(moon)
        MERGE (luna2)-[:FIRST_IMPACT]->(moon)
        
        // Mars 2020 - Perseverance
        MERGE (mars2020:Mission {name: 'Mars 2020', launch_date: '2020-07-30', mission_type: 'uncrewed', status: 'active'})
        MERGE (mars2020)-[:LAUNCHED_BY]->(nasa)
        MERGE (mars2020)-[:TARGETED]->(mars)
        
        MERGE (perseverance:Spacecraft {name: 'Perseverance', type: 'rover', launch_date: '2020-07-30', landing_date: '2021-02-18'})
        MERGE (perseverance)-[:PART_OF]->(mars2020)
        MERGE (perseverance)-[:OPERATES_ON]->(mars)
        
        MERGE (ingenuity:Spacecraft {name: 'Ingenuity', type: 'helicopter', mission: 'Mars 2020'})
        MERGE (ingenuity)-[:PART_OF]->(mars2020)
        MERGE (ingenuity)-[:COMPANION_OF]->(perseverance)
        
        MERGE (first_flight:Event {name: 'First Powered Flight on Mars', date: '2021-04-19', type: 'flight'})
        MERGE (first_flight)-[:PART_OF]->(mars2020)
        MERGE (first_flight)-[:AT]->(mars)
        MERGE (ingenuity)-[:PERFORMED]->(first_flight)
        
        // Voyager 1
        MERGE (voyager1:Mission {name: 'Voyager 1', launch_date: '1977-09-05', mission_type: 'uncrewed', status: 'active'})
        MERGE (voyager1)-[:LAUNCHED_BY]->(nasa)
        
        MERGE (voyager_probe:Spacecraft {name: 'Voyager 1', type: 'space_probe'})
        MERGE (voyager_probe)-[:PART_OF]->(voyager1)
        
        MERGE (voyager1)-[:TARGETED]->(jupiter)
        MERGE (voyager1)-[:TARGETED]->(saturn)
        
        MERGE (jupiter_flyby:Event {name: 'Jupiter Flyby', date: '1979-03-05', type: 'flyby'})
        MERGE (jupiter_flyby)-[:PART_OF]->(voyager1)
        MERGE (jupiter_flyby)-[:AT]->(jupiter)
        
        MERGE (saturn_flyby:Event {name: 'Saturn Flyby', date: '1980-11-12', type: 'flyby'})
        MERGE (saturn_flyby)-[:PART_OF]->(voyager1)
        MERGE (saturn_flyby)-[:AT]->(saturn)
        
        MERGE (interstellar:Event {name: 'Entered Interstellar Space', date: '2012-08-25', type: 'milestone'})
        MERGE (interstellar)-[:PART_OF]->(voyager1)
        MERGE (voyager_probe)-[:ACHIEVED]->(interstellar)
        
        // Venera 7 - Venus
        MERGE (venera7:Mission {name: 'Venera 7', launch_date: '1970-08-17', mission_type: 'uncrewed', status: 'success'})
        MERGE (venera7)-[:LAUNCHED_BY]->(soviets)
        MERGE (venera7)-[:TARGETED]->(venus)
        
        MERGE (venus_landing:Event {name: 'First Venus Soft Landing', date: '1970-12-15', type: 'landing'})
        MERGE (venus_landing)-[:PART_OF]->(venera7)
        MERGE (venus_landing)-[:AT]->(venus)
        
        // Cassini-Huygens - Saturn
        MERGE (cassini:Mission {name: 'Cassini-Huygens', launch_date: '1997-10-15', mission_type: 'uncrewed', status: 'completed'})
        MERGE (cassini)-[:LAUNCHED_BY]->(nasa)
        MERGE (cassini)-[:COLLABORATOR]->(esa)
        MERGE (cassini)-[:TARGETED]->(saturn)
        
        MERGE (cassini_spacecraft:Spacecraft {name: 'Cassini', type: 'orbiter'})
        MERGE (huygens:Spacecraft {name: 'Huygens', type: 'lander'})
        MERGE (cassini_spacecraft)-[:PART_OF]->(cassini)
        MERGE (huygens)-[:PART_OF]->(cassini)
        MERGE (huygens)-[:BUILT_BY]->(esa)
        
        MERGE (titan_landing:Event {name: 'Titan Landing', date: '2005-01-14', type: 'landing'})
        MERGE (titan_landing)-[:PART_OF]->(cassini)
        MERGE (huygens)-[:PERFORMED]->(titan_landing)
        
        // Juno - Jupiter
        MERGE (juno:Mission {name: 'Juno', launch_date: '2011-08-05', mission_type: 'uncrewed', status: 'active'})
        MERGE (juno)-[:LAUNCHED_BY]->(nasa)
        MERGE (juno)-[:TARGETED]->(jupiter)
        
        MERGE (juno_spacecraft:Spacecraft {name: 'Juno', type: 'orbiter'})
        MERGE (juno_spacecraft)-[:PART_OF]->(juno)
        
        // Rosetta - Comet
        MERGE (rosetta:Mission {name: 'Rosetta', launch_date: '2004-03-02', mission_type: 'uncrewed', status: 'completed'})
        MERGE (rosetta)-[:LAUNCHED_BY]->(esa)
        MERGE (rosetta)-[:TARGETED]->(comet67p)
        
        MERGE (philae:Spacecraft {name: 'Philae', type: 'lander'})
        MERGE (philae)-[:PART_OF]->(rosetta)
        
        MERGE (comet_landing:Event {name: 'First Comet Landing', date: '2014-11-12', type: 'landing'})
        MERGE (comet_landing)-[:PART_OF]->(rosetta)
        MERGE (philae)-[:PERFORMED]->(comet_landing)
        MERGE (comet_landing)-[:AT]->(comet67p)
        
        // Tianwen-1 - Mars
        MERGE (tianwen1:Mission {name: 'Tianwen-1', launch_date: '2020-07-23', mission_type: 'uncrewed', status: 'active'})
        MERGE (tianwen1)-[:LAUNCHED_BY]->(cnsa)
        MERGE (tianwen1)-[:TARGETED]->(mars)
        
        // Hope - Mars
        MERGE (hope:Mission {name: 'Emirates Mars Mission (Hope)', launch_date: '2020-07-19', mission_type: 'uncrewed', status: 'active'})
        MERGE (hope)-[:LAUNCHED_BY]->(uaesa)
        MERGE (hope)-[:TARGETED]->(mars)
        
        RETURN {
            organizations: count(DISTINCT [nasa, esa, spacex, roscosmos, jaxa, cnsa, soviets, uaesa]),
            missions: count(DISTINCT [apollo11, luna2, mars2020, voyager1, venera7, cassini, juno, rosetta, tianwen1, hope]),
            spacecraft: count(DISTINCT [eagle, perseverance, ingenuity, voyager_probe, cassini_spacecraft, huygens, juno_spacecraft, philae]),
            celestial_bodies: count(DISTINCT [mars, moon, venus, jupiter, saturn, mercury, comet67p]),
            events: count(DISTINCT [first_steps, luna2, first_flight, interstellar, venus_landing, titan_landing, comet_landing])
        } as counts
        """
        
        try:
            with self._get_driver().session() as session:
                result = session.run(cypher_query)
                counts = result.single()["counts"]
                
                return {
                    "status": "success",
                    "message": "Basic subgraph seeded successfully",
                    "node_counts": {
                        "organizations": counts["organizations"],
                        "missions": counts["missions"],
                        "spacecraft": counts["spacecraft"],
                        "celestial_bodies": counts["celestial_bodies"],
                        "events": counts["events"]
                    },
                    "total_nodes": sum(counts.values())
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "node_counts": {},
                "total_nodes": 0
            }
    
    def get_exploration_context(self, celestial_body: str) -> Dict[str, Any]:
        """Get exploration context for a celestial body."""
        query = """
        MATCH (body:CelestialBody {name: $body_name})
        OPTIONAL MATCH (body)<-[:TARGETED]-(mission:Mission)
        OPTIONAL MATCH (body)<-[:AT]-(event:Event)
        OPTIONAL MATCH (body)<-[:OPERATES_ON]-(spacecraft:Spacecraft)
        OPTIONAL MATCH (body)<-[:PART_OF]-(:Mission)<-[:LAUNCHED_BY]-(org:Organization)
        
        WITH body, collect(DISTINCT mission) as missions, 
                  collect(DISTINCT event) as events, 
                  collect(DISTINCT spacecraft) as spacecraft, 
                  collect(DISTINCT org) as organizations
        
        RETURN {
            body: {
                name: body.name,
                type: body.type,
                discovered: body.discovered
            },
            missions: [m in missions | {
                name: m.name,
                launch_date: m.launch_date,
                mission_type: m.mission_type,
                status: m.status
            }],
            spacecraft: [s in spacecraft | {
                name: s.name,
                type: s.type,
                mission: s.mission,
                launch_date: s.launch_date,
                landing_date: s.landing_date
            }],
            events: [e in events | {
                name: e.name,
                date: e.date,
                type: e.type
            }],
            organizations: [o in organizations | {
                name: o.name,
                country: o.country,
                founded: o.founded
            }]
        } as context
        """

        try:
            with self._get_driver().session() as session:
                result = session.run(query, body_name=celestial_body)
                record = result.single()

                if record is None or record["context"] is None:
                    return {
                        "status": "not_found",
                        "celestial_body": celestial_body,
                        "message": f"No exploration data found for {celestial_body}",
                        "context": {
                            "body": {"name": celestial_body},
                            "missions": [],
                            "spacecraft": [],
                            "events": [],
                            "organizations": []
                        }
                    }

                return {
                    "status": "success",
                    "context": record["context"]
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "celestial_body": celestial_body
            }
    
    def get_mission_history(self, celestial_body: str, limit: int = 50) -> Dict[str, Any]:
        """Get mission history for a celestial body."""
        query = """
        MATCH (body:CelestialBody {name: $body_name})<-[:TARGETED]-(mission:Mission)
        OPTIONAL MATCH (mission)-[:LAUNCHED_BY]->(org:Organization)
        OPTIONAL MATCH (mission)-[:USED_SPACECRAFT|PART_OF]->(sc:Spacecraft)
        
        RETURN {
            mission: {
                name: mission.name,
                launch_date: mission.launch_date,
                mission_type: mission.mission_type,
                status: mission.status
            },
            organization: {
                name: org.name,
                country: org.country
            },
            spacecraft: [s in collect(DISTINCT sc) | {
                name: s.name,
                type: s.type
            }]
        } as mission_data
        
        ORDER BY mission.launch_date ASC
        LIMIT $limit
        """
        
        try:
            with self._get_driver().session() as session:
                result = session.run(query, body_name=celestial_body, limit=limit)
                missions = [record["mission_data"] for record in result]
                
                return {
                    "status": "success",
                    "celestial_body": celestial_body,
                    "missions": missions,
                    "count": len(missions)
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "celestial_body": celestial_body,
                "missions": [],
                "count": 0
            }
    
    def query(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a custom Cypher query."""
        try:
            with self._get_driver().session() as session:
                result = session.run(cypher, **(parameters or {}))
                records = [dict(record) for record in result]
                
                return {
                    "status": "success",
                    "records": records,
                    "count": len(records)
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "records": [],
                "count": 0
            }
    
    def get_all_celestial_bodies(self) -> List[Dict[str, Any]]:
        """Get all celestial bodies from the graph."""
        query = "MATCH (body:CelestialBody) RETURN body.name as name, body.type as type, body.discovered as discovered ORDER BY body.name"
        try:
            with self._get_driver().session() as session:
                result = session.run(query)
                return [{"name": record["name"], "type": record["type"], "discovered": record["discovered"]} for record in result]
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_all_missions(self) -> List[Dict[str, Any]]:
        """Get all missions from the graph."""
        query = "MATCH (m:Mission) RETURN m.name as name, m.launch_date as launch_date, m.mission_type as mission_type, m.status as status ORDER BY m.launch_date"
        try:
            with self._get_driver().session() as session:
                result = session.run(query)
                return [{"name": record["name"], "launch_date": record["launch_date"], "mission_type": record["mission_type"], "status": record["status"]} for record in result]
        except Exception as e:
            return [{"error": str(e)}]


# Global service instance
graph_service = GraphService()
