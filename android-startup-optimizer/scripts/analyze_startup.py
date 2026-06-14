#!/usr/bin/env python3
"""
Analyze Perfetto trace files for startup bottlenecks.

Usage:
    python analyze_startup.py trace.perfetto

Identifies:
- Main thread blocking operations
- Binder transactions
- GC events
- Layout inflation
- Class loading
- Disk I/O
"""

import sqlite3
import sys
from pathlib import Path


class StartupAnalyzer:
    def __init__(self, trace_path: str):
        self.trace_path = Path(trace_path)
        if not self.trace_path.exists():
            raise FileNotFoundError(f"Trace file not found: {trace_path}")

        # Convert perfetto to sqlite if needed
        self.db_path = self.trace_path.with_suffix(".db")
        if not self.db_path.exists():
            print("Converting trace to SQLite...")
            self._convert_to_sqlite()

        self.conn = sqlite3.connect(str(self.db_path))
        self.cursor = self.conn.cursor()

    def _convert_to_sqlite(self):
        """Convert Perfetto trace to SQLite database."""
        import subprocess

        try:
            subprocess.run(
                ["trace_processor_shell", "--httpd", str(self.trace_path)], check=True
            )
        except FileNotFoundError:
            print("Error: trace_processor_shell not found")
            print("Install from: https://perfetto.dev/docs/quickstart/trace-analysis")
            sys.exit(1)

    def analyze(self):
        """Run all analyses."""
        print("=" * 80)
        print("ANDROID STARTUP ANALYSIS")
        print("=" * 80)
        print()

        self._analyze_main_thread_blocking()
        self._analyze_binder_transactions()
        self._analyze_gc_events()
        self._analyze_class_loading()
        self._analyze_layout_inflation()

        print()
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        self._generate_recommendations()

    def _analyze_main_thread_blocking(self):
        """Find operations blocking the main thread."""
        print("Main Thread Blocking Operations (>20ms)")
        print("-" * 80)

        query = """
        SELECT 
            name,
            dur / 1e6 as duration_ms,
            ts / 1e9 as timestamp_s
        FROM slice
        WHERE 
            name LIKE '%main%'
            AND dur > 20000000
        ORDER BY dur DESC
        LIMIT 10
        """

        results = self.cursor.execute(query).fetchall()

        if results:
            for name, duration, timestamp in results:
                print(f"  {duration:>8.2f}ms @ {timestamp:>8.2f}s - {name}")
        else:
            print("  ✓ No significant blocking operations found")
        print()

    def _analyze_binder_transactions(self):
        """Analyze binder IPC calls."""
        print("Binder Transactions (>10ms)")
        print("-" * 80)

        query = """
        SELECT 
            name,
            dur / 1e6 as duration_ms,
            COUNT(*) as count
        FROM slice
        WHERE 
            name LIKE '%binder%'
            AND dur > 10000000
        GROUP BY name
        ORDER BY duration_ms DESC
        LIMIT 10
        """

        results = self.cursor.execute(query).fetchall()

        if results:
            for name, duration, count in results:
                print(f"  {duration:>8.2f}ms ({count}x) - {name}")
        else:
            print("  ✓ No slow binder transactions found")
        print()

    def _analyze_gc_events(self):
        """Analyze garbage collection events."""
        print("Garbage Collection Events")
        print("-" * 80)

        query = """
        SELECT 
            name,
            dur / 1e6 as duration_ms,
            COUNT(*) as count
        FROM slice
        WHERE 
            name LIKE '%GC%'
            OR name LIKE '%garbage%'
        GROUP BY name
        ORDER BY duration_ms DESC
        """

        results = self.cursor.execute(query).fetchall()

        if results:
            total_gc_time = sum(r[1] for r in results)
            print(f"  Total GC time: {total_gc_time:.2f}ms")
            for name, duration, count in results[:5]:
                print(f"  {duration:>8.2f}ms ({count}x) - {name}")
        else:
            print("  ✓ No GC events found")
        print()

    def _analyze_class_loading(self):
        """Analyze class loading operations."""
        print("Class Loading Operations")
        print("-" * 80)

        query = """
        SELECT 
            name,
            dur / 1e6 as duration_ms,
            COUNT(*) as count
        FROM slice
        WHERE 
            name LIKE '%ClassLoader%'
            OR name LIKE '%loadClass%'
            OR name LIKE '%dex%'
        GROUP BY name
        ORDER BY duration_ms DESC
        LIMIT 10
        """

        results = self.cursor.execute(query).fetchall()

        if results:
            for name, duration, count in results:
                print(f"  {duration:>8.2f}ms ({count}x) - {name}")
        else:
            print("  ✓ No significant class loading found")
        print()

    def _analyze_layout_inflation(self):
        """Analyze layout inflation."""
        print("Layout Inflation")
        print("-" * 80)

        query = """
        SELECT 
            name,
            dur / 1e6 as duration_ms
        FROM slice
        WHERE 
            name LIKE '%inflate%'
            OR name LIKE '%Layout%'
        ORDER BY dur DESC
        LIMIT 10
        """

        results = self.cursor.execute(query).fetchall()

        if results:
            for name, duration in results:
                print(f"  {duration:>8.2f}ms - {name}")
        else:
            print("  ✓ No layout inflation found (likely using Compose)")
        print()

    def _generate_recommendations(self):
        """Generate optimization recommendations."""
        recommendations = []

        # Check for main thread blocking
        blocking_query = """
        SELECT COUNT(*) FROM slice
        WHERE name LIKE '%main%' AND dur > 20000000
        """
        blocking_count = self.cursor.execute(blocking_query).fetchone()[0]

        if blocking_count > 5:
            recommendations.append(
                "⚠️  High main thread blocking detected\n"
                "   → Move heavy operations to background threads (Dispatchers.IO)\n"
                "   → Use Jetpack App Startup for SDK initialization"
            )

        # Check for GC pressure
        gc_query = """
        SELECT SUM(dur) / 1e6 FROM slice
        WHERE name LIKE '%GC%'
        """
        gc_time = self.cursor.execute(gc_query).fetchone()[0] or 0

        if gc_time > 100:
            recommendations.append(
                f"⚠️  High GC pressure ({gc_time:.0f}ms total)\n"
                "   → Reduce object allocations during startup\n"
                "   → Use object pooling for frequently created objects\n"
                "   → Consider using primitive types instead of boxed types"
            )

        # Check for binder transactions
        binder_query = """
        SELECT COUNT(*) FROM slice
        WHERE name LIKE '%binder%' AND dur > 10000000
        """
        binder_count = self.cursor.execute(binder_query).fetchone()[0]

        if binder_count > 10:
            recommendations.append(
                "⚠️  Many slow binder transactions detected\n"
                "   → Reduce IPC calls during startup\n"
                "   → Cache results from system services\n"
                "   → Defer non-critical service calls"
            )

        if recommendations:
            for rec in recommendations:
                print(rec)
                print()
        else:
            print("✓ No major issues detected!")
            print()
            print("Consider these optimizations:")
            print("  • Generate Baseline Profiles")
            print("  • Create Startup Profiles")
            print("  • Enable R8 full mode")
            print("  • Use lazy dependency injection")

    def close(self):
        """Close database connection."""
        self.conn.close()


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_startup.py <trace.perfetto>")
        sys.exit(1)

    trace_path = sys.argv[1]

    try:
        analyzer = StartupAnalyzer(trace_path)
        analyzer.analyze()
        analyzer.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
