namespace Godding.Models;

public class Node
{
    public long Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Content { get; set; }
    public string Type { get; set; } = "function";
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }

    public override string ToString()
    {
        var typeTag = Type == "component" ? "[C]" : "[F]";
        return $"{typeTag} #{Id} {Name}";
    }
}
