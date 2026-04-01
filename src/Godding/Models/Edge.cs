namespace Godding.Models;

public class Edge
{
    public long Id { get; set; }
    public long ParentId { get; set; }
    public long ChildId { get; set; }
    public double Weight { get; set; } = 1.0;
    public DateTime CreatedAt { get; set; }
}
