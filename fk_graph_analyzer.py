"""
FK-Graph Analyzer with NetworkX
Implements Task 1.2 from the roadmap - schema relationship graph analysis
for optimal JOIN path discovery and complex multi-table query support.
"""

import networkx as nx
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class JoinPath:
    """Represents a JOIN path between tables."""
    source: str
    target: str
    path: List[str]
    joins: List[str]
    complexity: int
    estimated_cost: float


@dataclass
class TableRelationship:
    """Represents a relationship between two tables."""
    from_table: str
    to_table: str
    from_column: str
    to_column: str
    relationship_type: str  # "one_to_many", "many_to_one", "many_to_many"
    weight: float = 1.0


class FKGraphAnalyzer:
    """
    Schema relationship graph analyzer using NetworkX.
    
    Builds a graph representation of database schema relationships
    and provides JOIN path finding algorithms for optimal query generation.
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.relationships: Dict[Tuple[str, str], TableRelationship] = {}
        self.table_metadata: Dict[str, Dict] = {}
        self._is_initialized = False
    
    def initialize_from_global_context(self) -> None:
        """Initialize the graph from global_context.py relationships."""
        try:
            from global_context import WINCASA_GLOBAL_CONTEXT
            
            # Extract relationships from global context
            relationships_data = WINCASA_GLOBAL_CONTEXT.get("core_relationships", {})
            
            # WINCASA core relationships based on global_context.py
            core_relationships = [
                # Primary entity relationships
                ("BEWOHNER", "OBJEKTE", "BWO", "ONR", "many_to_one", 1.0),
                ("EIGENTUEMER", "VEREIG", "EIGNR", "EIGNR", "one_to_many", 1.0), 
                ("VEREIG", "OBJEKTE", "ONR", "ONR", "many_to_one", 1.0),
                ("OBJEKTE", "WOHNUNG", "ONR", "ONR", "one_to_many", 1.0),
                
                # Financial relationships
                ("KONTEN", "BUCHUNG", "KNR", "BKNR", "one_to_many", 1.0),
                ("BUCHUNG", "SOLLSTELLUNG", "LFDNR", "LFDNR", "many_to_one", 1.0),
                ("OBJEKTE", "KONTEN", "ONR", "BEZKONR", "one_to_many", 1.2),
                
                # Address and location
                ("OBJEKTE", "ORT", "ORTNR", "ORTNR", "many_to_one", 1.1),
                ("BEWOHNER", "ORT", "ORTNR", "ORTNR", "many_to_one", 1.1),
                
                # Property management
                ("OBJEKTE", "OBJEKTART", "OARTNR", "OARTNR", "many_to_one", 1.1),
                ("WOHNUNG", "WHGART", "WGART", "WGART", "many_to_one", 1.1),
                
                # Utility connections (higher complexity)
                ("BEWOHNER", "KONTEN", "BWO", "BEZKONR", "many_to_many", 2.0),
                ("EIGENTUEMER", "KONTEN", "EIGNR", "BEZKONR", "many_to_many", 2.0),
            ]
            
            for rel in core_relationships:
                self.add_relationship(
                    from_table=rel[0],
                    to_table=rel[1], 
                    from_column=rel[2],
                    to_column=rel[3],
                    relationship_type=rel[4],
                    weight=rel[5]
                )
            
            self._is_initialized = True
            print(f"✓ FKGraphAnalyzer: Initialized with {len(core_relationships)} relationships")
            
        except ImportError:
            print("⚠️ FKGraphAnalyzer: global_context.py not found, using fallback relationships")
            self._initialize_fallback_relationships()
    
    def _initialize_fallback_relationships(self) -> None:
        """Fallback relationships if global_context is not available."""
        fallback_relationships = [
            ("BEWOHNER", "OBJEKTE", "BWO", "ONR", "many_to_one", 1.0),
            ("EIGENTUEMER", "OBJEKTE", "EIGNR", "ONR", "many_to_one", 1.5),
            ("OBJEKTE", "WOHNUNG", "ONR", "ONR", "one_to_many", 1.0),
            ("KONTEN", "BUCHUNG", "KNR", "BKNR", "one_to_many", 1.0),
        ]
        
        for rel in fallback_relationships:
            self.add_relationship(
                from_table=rel[0],
                to_table=rel[1],
                from_column=rel[2], 
                to_column=rel[3],
                relationship_type=rel[4],
                weight=rel[5]
            )
        
        self._is_initialized = True
        print(f"✓ FKGraphAnalyzer: Initialized with {len(fallback_relationships)} fallback relationships")
    
    def add_relationship(
        self,
        from_table: str,
        to_table: str,
        from_column: str,
        to_column: str,
        relationship_type: str = "many_to_one",
        weight: float = 1.0
    ) -> None:
        """Add a relationship between two tables to the graph."""
        
        # Add nodes if they don't exist
        if not self.graph.has_node(from_table):
            self.graph.add_node(from_table)
        if not self.graph.has_node(to_table):
            self.graph.add_node(to_table)
        
        # Add edge with relationship metadata
        self.graph.add_edge(
            from_table, 
            to_table,
            from_column=from_column,
            to_column=to_column,
            weight=weight,
            relationship_type=relationship_type
        )
        
        # Store detailed relationship info
        key = (from_table, to_table)
        self.relationships[key] = TableRelationship(
            from_table=from_table,
            to_table=to_table,
            from_column=from_column,
            to_column=to_column,
            relationship_type=relationship_type,
            weight=weight
        )
    
    def find_join_path(self, from_table: str, to_table: str) -> Optional[JoinPath]:
        """
        Find the optimal JOIN path between two tables.
        
        Args:
            from_table: Source table name
            to_table: Target table name
            
        Returns:
            JoinPath object with optimal path details, or None if no path exists
        """
        if not self._is_initialized:
            self.initialize_from_global_context()
        
        try:
            # Find shortest path based on edge weights
            path = nx.shortest_path(
                self.graph, 
                from_table.upper(), 
                to_table.upper(),
                weight='weight'
            )
            
            if len(path) < 2:
                return None
            
            # Generate JOIN statements for the path
            joins = []
            total_cost = 0.0
            
            for i in range(len(path) - 1):
                source = path[i]
                target = path[i + 1]
                
                if self.graph.has_edge(source, target):
                    edge_data = self.graph[source][target]
                    from_col = edge_data['from_column']
                    to_col = edge_data['to_column']
                    weight = edge_data['weight']
                    
                    join_sql = f"JOIN {target} ON {source}.{from_col} = {target}.{to_col}"
                    joins.append(join_sql)
                    total_cost += weight
                else:
                    # Try reverse direction
                    if self.graph.has_edge(target, source):
                        edge_data = self.graph[target][source]
                        from_col = edge_data['to_column']
                        to_col = edge_data['from_column']
                        weight = edge_data['weight']
                        
                        join_sql = f"JOIN {target} ON {source}.{from_col} = {target}.{to_col}"
                        joins.append(join_sql)
                        total_cost += weight
            
            return JoinPath(
                source=from_table,
                target=to_table,
                path=path,
                joins=joins,
                complexity=len(path) - 1,
                estimated_cost=total_cost
            )
            
        except nx.NetworkXNoPath:
            print(f"⚠️ No path found between {from_table} and {to_table}")
            return None
        except Exception as e:
            print(f"⚠️ Error finding path between {from_table} and {to_table}: {e}")
            return None
    
    def get_all_related_tables(
        self, 
        tables: List[str], 
        max_hops: int = 2
    ) -> Set[str]:
        """
        Find all tables related to the given tables within max_hops.
        
        Args:
            tables: List of source table names
            max_hops: Maximum number of hops to explore
            
        Returns:
            Set of all related table names
        """
        if not self._is_initialized:
            self.initialize_from_global_context()
        
        related_tables = set()
        for table in tables:
            table_upper = table.upper()
            if self.graph.has_node(table_upper):
                # Get neighbors within max_hops using ego_graph
                ego = nx.ego_graph(self.graph, table_upper, radius=max_hops)
                related_tables.update(ego.nodes())
            else:
                related_tables.add(table_upper)
        
        return related_tables
    
    def generate_join_sql(self, tables: List[str], base_table: Optional[str] = None) -> str:
        """
        Generate optimized JOIN SQL for multiple tables.
        
        Args:
            tables: List of table names to join
            base_table: Optional base table to start from
            
        Returns:
            SQL JOIN clauses as a string
        """
        if not self._is_initialized:
            self.initialize_from_global_context()
        
        if len(tables) < 2:
            return ""
        
        # Determine base table if not provided
        if base_table is None:
            # Use the table with most connections as base
            table_degrees = {}
            for table in tables:
                table_upper = table.upper()
                if self.graph.has_node(table_upper):
                    table_degrees[table_upper] = self.graph.degree(table_upper)
                else:
                    table_degrees[table_upper] = 0
            base_table = max(table_degrees, key=table_degrees.get)
        else:
            base_table = base_table.upper()
        
        # Find optimal JOIN order using minimum spanning tree approach
        remaining_tables = [t.upper() for t in tables if t.upper() != base_table]
        joined_tables = {base_table}
        join_clauses = []
        
        while remaining_tables:
            best_join = None
            best_cost = float('inf')
            
            for remaining in remaining_tables:
                for joined in joined_tables:
                    # Try to find path between remaining and any joined table
                    join_path = self.find_join_path(joined, remaining)
                    if join_path and join_path.estimated_cost < best_cost:
                        best_cost = join_path.estimated_cost
                        best_join = (remaining, join_path)
            
            if best_join:
                table_to_join, path = best_join
                # Add the direct JOIN for this table
                if path.joins:
                    join_clauses.extend(path.joins)
                joined_tables.add(table_to_join)
                remaining_tables.remove(table_to_join)
            else:
                # No path found, add remaining tables with warning
                for remaining in remaining_tables:
                    join_clauses.append(f"-- WARNING: No path found for {remaining}")
                break
        
        return "\n".join(join_clauses)
    
    def analyze_query_complexity(self, tables: List[str]) -> Dict:
        """
        Analyze the complexity of joining the given tables.
        
        Args:
            tables: List of table names
            
        Returns:
            Dictionary with complexity analysis
        """
        if not self._is_initialized:
            self.initialize_from_global_context()
        
        analysis = {
            "table_count": len(tables),
            "total_joins_needed": len(tables) - 1 if len(tables) > 1 else 0,
            "complexity_score": 0.0,
            "missing_relationships": [],
            "optimization_suggestions": []
        }
        
        if len(tables) < 2:
            return analysis
        
        # Calculate complexity based on JOIN paths
        total_complexity = 0.0
        base_table = tables[0].upper()
        
        for i, table in enumerate(tables[1:], 1):
            table_upper = table.upper()
            join_path = self.find_join_path(base_table, table_upper)
            
            if join_path:
                total_complexity += join_path.estimated_cost
            else:
                analysis["missing_relationships"].append(f"{base_table} -> {table_upper}")
                total_complexity += 10.0  # High penalty for missing relationship
        
        analysis["complexity_score"] = total_complexity
        
        # Add optimization suggestions
        if total_complexity > 5.0:
            analysis["optimization_suggestions"].append("Consider using a different base table")
        if len(analysis["missing_relationships"]) > 0:
            analysis["optimization_suggestions"].append("Some table relationships are missing or indirect")
        if len(tables) > 5:
            analysis["optimization_suggestions"].append("Consider breaking query into smaller parts")
        
        return analysis
    
    def get_graph_statistics(self) -> Dict:
        """Get statistics about the relationship graph."""
        if not self._is_initialized:
            self.initialize_from_global_context()
        
        return {
            "total_tables": self.graph.number_of_nodes(),
            "total_relationships": self.graph.number_of_edges(),
            "average_connections_per_table": self.graph.number_of_edges() / max(1, self.graph.number_of_nodes()),
            "most_connected_tables": sorted(
                self.graph.degree(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5],
            "isolated_tables": [node for node in self.graph.nodes() if self.graph.degree(node) == 0]
        }
    
    def export_graph_to_json(self, filepath: str) -> None:
        """Export the graph structure to JSON for visualization."""
        if not self._is_initialized:
            self.initialize_from_global_context()
        
        graph_data = {
            "nodes": [
                {"id": node, "degree": self.graph.degree(node)}
                for node in self.graph.nodes()
            ],
            "edges": [
                {
                    "source": edge[0],
                    "target": edge[1],
                    "from_column": self.graph[edge[0]][edge[1]].get("from_column", ""),
                    "to_column": self.graph[edge[0]][edge[1]].get("to_column", ""),
                    "weight": self.graph[edge[0]][edge[1]].get("weight", 1.0),
                    "relationship_type": self.graph[edge[0]][edge[1]].get("relationship_type", "unknown")
                }
                for edge in self.graph.edges()
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        print(f"✓ Graph exported to {filepath}")


# Global instance for use across the application
fk_graph_analyzer = FKGraphAnalyzer()


def get_join_path(from_table: str, to_table: str) -> Optional[JoinPath]:
    """Convenience function to get JOIN path between two tables."""
    return fk_graph_analyzer.find_join_path(from_table, to_table)


def get_related_tables(tables: List[str], max_hops: int = 2) -> Set[str]:
    """Convenience function to get all related tables."""
    return fk_graph_analyzer.get_all_related_tables(tables, max_hops)


def generate_optimal_joins(tables: List[str], base_table: Optional[str] = None) -> str:
    """Convenience function to generate optimal JOIN SQL."""
    return fk_graph_analyzer.generate_join_sql(tables, base_table)


if __name__ == "__main__":
    # Test the FK Graph Analyzer
    analyzer = FKGraphAnalyzer()
    analyzer.initialize_from_global_context()
    
    # Test basic functionality
    print("\n=== FK Graph Analyzer Test ===")
    
    # Test JOIN path finding
    path = analyzer.find_join_path("BEWOHNER", "KONTEN")
    if path:
        print(f"Path from BEWOHNER to KONTEN:")
        print(f"  Tables: {' -> '.join(path.path)}")
        print(f"  JOINs: {path.joins}")
        print(f"  Complexity: {path.complexity}")
        print(f"  Cost: {path.estimated_cost}")
    
    # Test related tables discovery
    related = analyzer.get_all_related_tables(["BEWOHNER"], max_hops=2)
    print(f"\nTables related to BEWOHNER (within 2 hops): {sorted(related)}")
    
    # Test JOIN SQL generation
    join_sql = analyzer.generate_join_sql(["BEWOHNER", "OBJEKTE", "EIGENTUEMER"])
    print(f"\nGenerated JOIN SQL:\n{join_sql}")
    
    # Test complexity analysis
    complexity = analyzer.analyze_query_complexity(["BEWOHNER", "OBJEKTE", "KONTEN", "BUCHUNG"])
    print(f"\nComplexity Analysis: {complexity}")
    
    # Export graph
    analyzer.export_graph_to_json("output/fk_graph.json")
    
    print("\n✓ FK Graph Analyzer test completed!")