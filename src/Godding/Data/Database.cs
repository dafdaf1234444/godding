using Microsoft.Data.Sqlite;
using Godding.Models;

namespace Godding.Data;

public class Database : IDisposable
{
    private readonly SqliteConnection _connection;

    public Database(string dbPath)
    {
        _connection = new SqliteConnection($"Data Source={dbPath}");
        _connection.Open();
        Initialize();
    }

    private void Initialize()
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                content TEXT,
                type TEXT NOT NULL DEFAULT 'function' CHECK(type IN ('function', 'component')),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
                child_id INTEGER NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
                weight REAL DEFAULT 1.0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(parent_id, child_id)
            );
            """;
        cmd.ExecuteNonQuery();
    }

    public long AddNode(string name, string? content, string type)
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = """
            INSERT INTO nodes (name, content, type) VALUES (@name, @content, @type);
            SELECT last_insert_rowid();
            """;
        cmd.Parameters.AddWithValue("@name", name);
        cmd.Parameters.AddWithValue("@content", (object?)content ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@type", type);
        return (long)cmd.ExecuteScalar()!;
    }

    public Node? GetNode(long id)
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = "SELECT id, name, content, type, created_at, updated_at FROM nodes WHERE id = @id";
        cmd.Parameters.AddWithValue("@id", id);
        using var reader = cmd.ExecuteReader();
        return reader.Read() ? ReadNode(reader) : null;
    }

    public Node? GetNodeByName(string name)
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = "SELECT id, name, content, type, created_at, updated_at FROM nodes WHERE name = @name";
        cmd.Parameters.AddWithValue("@name", name);
        using var reader = cmd.ExecuteReader();
        return reader.Read() ? ReadNode(reader) : null;
    }

    public List<Node> GetAllNodes()
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = "SELECT id, name, content, type, created_at, updated_at FROM nodes ORDER BY id";
        return ReadNodes(cmd);
    }

    public List<Node> SearchNodes(string query)
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = """
            SELECT id, name, content, type, created_at, updated_at FROM nodes
            WHERE name LIKE @q OR content LIKE @q
            ORDER BY id
            """;
        cmd.Parameters.AddWithValue("@q", $"%{query}%");
        return ReadNodes(cmd);
    }

    public bool DeleteNode(long id)
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = "DELETE FROM nodes WHERE id = @id";
        cmd.Parameters.AddWithValue("@id", id);
        return cmd.ExecuteNonQuery() > 0;
    }

    public bool UpdateNode(long id, string? name, string? content, string? type)
    {
        var node = GetNode(id);
        if (node == null) return false;

        using var cmd = _connection.CreateCommand();
        cmd.CommandText = """
            UPDATE nodes SET name = @name, content = @content, type = @type,
            updated_at = datetime('now') WHERE id = @id
            """;
        cmd.Parameters.AddWithValue("@id", id);
        cmd.Parameters.AddWithValue("@name", name ?? node.Name);
        cmd.Parameters.AddWithValue("@content", (object?)(content ?? node.Content) ?? DBNull.Value);
        cmd.Parameters.AddWithValue("@type", type ?? node.Type);
        return cmd.ExecuteNonQuery() > 0;
    }

    public long AddEdge(long parentId, long childId, double weight = 1.0)
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = """
            INSERT INTO edges (parent_id, child_id, weight) VALUES (@parent, @child, @weight);
            SELECT last_insert_rowid();
            """;
        cmd.Parameters.AddWithValue("@parent", parentId);
        cmd.Parameters.AddWithValue("@child", childId);
        cmd.Parameters.AddWithValue("@weight", weight);
        return (long)cmd.ExecuteScalar()!;
    }

    public bool RemoveEdge(long parentId, long childId)
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = "DELETE FROM edges WHERE parent_id = @parent AND child_id = @child";
        cmd.Parameters.AddWithValue("@parent", parentId);
        cmd.Parameters.AddWithValue("@child", childId);
        return cmd.ExecuteNonQuery() > 0;
    }

    public List<Node> GetChildren(long parentId)
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = """
            SELECT n.id, n.name, n.content, n.type, n.created_at, n.updated_at
            FROM nodes n JOIN edges e ON n.id = e.child_id
            WHERE e.parent_id = @parent ORDER BY n.id
            """;
        cmd.Parameters.AddWithValue("@parent", parentId);
        return ReadNodes(cmd);
    }

    public List<Node> GetParents(long childId)
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = """
            SELECT n.id, n.name, n.content, n.type, n.created_at, n.updated_at
            FROM nodes n JOIN edges e ON n.id = e.parent_id
            WHERE e.child_id = @child ORDER BY n.id
            """;
        cmd.Parameters.AddWithValue("@child", childId);
        return ReadNodes(cmd);
    }

    public List<Node> GetRoots()
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = """
            SELECT id, name, content, type, created_at, updated_at FROM nodes
            WHERE id NOT IN (SELECT child_id FROM edges)
            ORDER BY id
            """;
        return ReadNodes(cmd);
    }

    public List<Node> GetLeaves()
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = """
            SELECT id, name, content, type, created_at, updated_at FROM nodes
            WHERE id NOT IN (SELECT parent_id FROM edges)
            ORDER BY id
            """;
        return ReadNodes(cmd);
    }

    public (int nodeCount, int edgeCount, int rootCount, int leafCount) GetStats()
    {
        using var cmd = _connection.CreateCommand();
        cmd.CommandText = "SELECT COUNT(*) FROM nodes";
        int nodes = Convert.ToInt32(cmd.ExecuteScalar());

        cmd.CommandText = "SELECT COUNT(*) FROM edges";
        int edges = Convert.ToInt32(cmd.ExecuteScalar());

        cmd.CommandText = "SELECT COUNT(*) FROM nodes WHERE id NOT IN (SELECT child_id FROM edges)";
        int roots = Convert.ToInt32(cmd.ExecuteScalar());

        cmd.CommandText = "SELECT COUNT(*) FROM nodes WHERE id NOT IN (SELECT parent_id FROM edges)";
        int leaves = Convert.ToInt32(cmd.ExecuteScalar());

        return (nodes, edges, roots, leaves);
    }

    private static Node ReadNode(SqliteDataReader reader) => new()
    {
        Id = reader.GetInt64(0),
        Name = reader.GetString(1),
        Content = reader.IsDBNull(2) ? null : reader.GetString(2),
        Type = reader.GetString(3),
        CreatedAt = DateTime.Parse(reader.GetString(4)),
        UpdatedAt = DateTime.Parse(reader.GetString(5))
    };

    private static List<Node> ReadNodes(SqliteCommand cmd)
    {
        var nodes = new List<Node>();
        using var reader = cmd.ExecuteReader();
        while (reader.Read())
            nodes.Add(ReadNode(reader));
        return nodes;
    }

    public void Dispose()
    {
        _connection?.Dispose();
    }
}
