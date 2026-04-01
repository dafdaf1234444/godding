using System.CommandLine;
using Godding.Data;
using Godding.Services;

var dbPathOption = new Option<string>(
    "--db",
    getDefaultValue: () => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.UserProfile),
        ".godding", "godding.db"),
    description: "Path to the SQLite database file");

var rootCommand = new RootCommand("Godding — the bidirectional tree. 1 becomes many, many become 1. The operation of transcendence itself.")
{
    dbPathOption
};

// ── add ──────────────────────────────────────────────────────────────
var addCommand = new Command("add", "Add a node to the tree");
var addNameArg = new Argument<string>("name", "Name of the node");
var addContentArg = new Argument<string?>("content", () => null, "Content/description of the node");
var addTypeOption = new Option<string>("--type", getDefaultValue: () => "function", "Node type: function (data+noise) or component (compressed)");
addTypeOption.AddAlias("-t");
addTypeOption.FromAmong("function", "component");
addCommand.AddArgument(addNameArg);
addCommand.AddArgument(addContentArg);
addCommand.AddOption(addTypeOption);
addCommand.AddOption(dbPathOption);

addCommand.SetHandler((name, content, type, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var id = db.AddNode(name, content, type);
    var tag = type == "component" ? "[C]" : "[F]";
    Console.WriteLine($"Created {tag} #{id} {name}");
}, addNameArg, addContentArg, addTypeOption, dbPathOption);

// ── link ─────────────────────────────────────────────────────────────
var linkCommand = new Command("link", "Link parent -> child (decomposition edge)");
var linkParentArg = new Argument<string>("parent", "Parent node (ID or name)");
var linkChildArg = new Argument<string>("child", "Child node (ID or name)");
linkCommand.AddArgument(linkParentArg);
linkCommand.AddArgument(linkChildArg);
linkCommand.AddOption(dbPathOption);

linkCommand.SetHandler((parentRef, childRef, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var svc = new TreeService(db);
    var parent = svc.ResolveNode(parentRef);
    var child = svc.ResolveNode(childRef);
    if (parent == null) { Console.WriteLine($"Parent not found: {parentRef}"); return; }
    if (child == null) { Console.WriteLine($"Child not found: {childRef}"); return; }

    try
    {
        db.AddEdge(parent.Id, child.Id);
        Console.WriteLine($"Linked: {parent} -> {child}");
    }
    catch (Microsoft.Data.Sqlite.SqliteException ex) when (ex.SqliteErrorCode == 19)
    {
        Console.WriteLine($"Link already exists: {parent} -> {child}");
    }
}, linkParentArg, linkChildArg, dbPathOption);

// ── unlink ───────────────────────────────────────────────────────────
var unlinkCommand = new Command("unlink", "Remove a link between parent and child");
var unlinkParentArg = new Argument<string>("parent", "Parent node (ID or name)");
var unlinkChildArg = new Argument<string>("child", "Child node (ID or name)");
unlinkCommand.AddArgument(unlinkParentArg);
unlinkCommand.AddArgument(unlinkChildArg);
unlinkCommand.AddOption(dbPathOption);

unlinkCommand.SetHandler((parentRef, childRef, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var svc = new TreeService(db);
    var parent = svc.ResolveNode(parentRef);
    var child = svc.ResolveNode(childRef);
    if (parent == null) { Console.WriteLine($"Parent not found: {parentRef}"); return; }
    if (child == null) { Console.WriteLine($"Child not found: {childRef}"); return; }

    if (db.RemoveEdge(parent.Id, child.Id))
        Console.WriteLine($"Unlinked: {parent} -/-> {child}");
    else
        Console.WriteLine($"No link found between {parent} and {child}");
}, unlinkParentArg, unlinkChildArg, dbPathOption);

// ── decompose (1 -> many) ────────────────────────────────────────────
var decomposeCommand = new Command("decompose", "1 -> many: show all descendants of a node");
decomposeCommand.AddAlias("dec");
var decNodeArg = new Argument<string>("node", "Node to decompose (ID or name)");
var decDepthOption = new Option<int>("--depth", getDefaultValue: () => 20, "Maximum depth");
decomposeCommand.AddArgument(decNodeArg);
decomposeCommand.AddOption(decDepthOption);
decomposeCommand.AddOption(dbPathOption);

decomposeCommand.SetHandler((nodeRef, depth, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var svc = new TreeService(db);
    var node = svc.ResolveNode(nodeRef);
    if (node == null) { Console.WriteLine($"Node not found: {nodeRef}"); return; }
    svc.PrintDecomposition(node.Id, depth);
}, decNodeArg, decDepthOption, dbPathOption);

// ── compose (many -> 1) ──────────────────────────────────────────────
var composeCommand = new Command("compose", "Many -> 1: trace all paths from a node back to its roots");
composeCommand.AddAlias("com");
var comNodeArg = new Argument<string>("node", "Node to compose from (ID or name)");
composeCommand.AddArgument(comNodeArg);
composeCommand.AddOption(dbPathOption);

composeCommand.SetHandler((nodeRef, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var svc = new TreeService(db);
    var node = svc.ResolveNode(nodeRef);
    if (node == null) { Console.WriteLine($"Node not found: {nodeRef}"); return; }
    svc.PrintComposition(node.Id);
}, comNodeArg, dbPathOption);

// ── tree ─────────────────────────────────────────────────────────────
var treeCommand = new Command("tree", "Show the full tree structure");
treeCommand.AddOption(dbPathOption);

treeCommand.SetHandler((dbPath) =>
{
    using var db = OpenDb(dbPath);
    var svc = new TreeService(db);
    svc.PrintFullTree();
}, dbPathOption);

// ── trace ────────────────────────────────────────────────────────────
var traceCommand = new Command("trace", "Find path between any two nodes");
var traceFromArg = new Argument<string>("from", "Start node (ID or name)");
var traceToArg = new Argument<string>("to", "End node (ID or name)");
traceCommand.AddArgument(traceFromArg);
traceCommand.AddArgument(traceToArg);
traceCommand.AddOption(dbPathOption);

traceCommand.SetHandler((fromRef, toRef, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var svc = new TreeService(db);
    var from = svc.ResolveNode(fromRef);
    var to = svc.ResolveNode(toRef);
    if (from == null) { Console.WriteLine($"Node not found: {fromRef}"); return; }
    if (to == null) { Console.WriteLine($"Node not found: {toRef}"); return; }
    svc.PrintTrace(from.Id, to.Id);
}, traceFromArg, traceToArg, dbPathOption);

// ── list ─────────────────────────────────────────────────────────────
var listCommand = new Command("list", "List all nodes");
listCommand.AddAlias("ls");
var listTypeOption = new Option<string?>("--type", "Filter by type: function or component");
listTypeOption.AddAlias("-t");
listCommand.AddOption(listTypeOption);
listCommand.AddOption(dbPathOption);

listCommand.SetHandler((type, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var nodes = db.GetAllNodes();
    if (type != null)
        nodes = nodes.Where(n => n.Type == type).ToList();

    if (nodes.Count == 0)
    {
        Console.WriteLine("(no nodes)");
        return;
    }

    foreach (var node in nodes)
    {
        var content = node.Content != null
            ? (node.Content.Length > 60 ? node.Content[..60] + "..." : node.Content)
            : "";
        Console.WriteLine($"  {node}  {content}");
    }
    Console.WriteLine($"\n  Total: {nodes.Count}");
}, listTypeOption, dbPathOption);

// ── show ─────────────────────────────────────────────────────────────
var showCommand = new Command("show", "Show details of a node");
var showNodeArg = new Argument<string>("node", "Node to show (ID or name)");
showCommand.AddArgument(showNodeArg);
showCommand.AddOption(dbPathOption);

showCommand.SetHandler((nodeRef, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var svc = new TreeService(db);
    var node = svc.ResolveNode(nodeRef);
    if (node == null) { Console.WriteLine($"Node not found: {nodeRef}"); return; }

    var parents = db.GetParents(node.Id);
    var children = db.GetChildren(node.Id);

    Console.WriteLine($"Node #{node.Id}");
    Console.WriteLine($"  Name:    {node.Name}");
    Console.WriteLine($"  Type:    {node.Type}");
    Console.WriteLine($"  Created: {node.CreatedAt}");
    Console.WriteLine($"  Updated: {node.UpdatedAt}");
    if (node.Content != null)
    {
        Console.WriteLine($"  Content:");
        foreach (var line in node.Content.Split('\n'))
            Console.WriteLine($"    {line}");
    }
    if (parents.Count > 0)
    {
        Console.WriteLine($"  Parents ({parents.Count}):");
        foreach (var p in parents)
            Console.WriteLine($"    <- {p}");
    }
    if (children.Count > 0)
    {
        Console.WriteLine($"  Children ({children.Count}):");
        foreach (var c in children)
            Console.WriteLine($"    -> {c}");
    }
}, showNodeArg, dbPathOption);

// ── search ───────────────────────────────────────────────────────────
var searchCommand = new Command("search", "Search nodes by name or content");
var searchQueryArg = new Argument<string>("query", "Search query");
searchCommand.AddArgument(searchQueryArg);
searchCommand.AddOption(dbPathOption);

searchCommand.SetHandler((query, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var results = db.SearchNodes(query);
    if (results.Count == 0)
    {
        Console.WriteLine($"No nodes matching '{query}'");
        return;
    }
    foreach (var node in results)
        Console.WriteLine($"  {node}");
    Console.WriteLine($"\n  Found: {results.Count}");
}, searchQueryArg, dbPathOption);

// ── delete ───────────────────────────────────────────────────────────
var deleteCommand = new Command("delete", "Delete a node and its edges");
deleteCommand.AddAlias("rm");
var deleteNodeArg = new Argument<string>("node", "Node to delete (ID or name)");
deleteCommand.AddArgument(deleteNodeArg);
deleteCommand.AddOption(dbPathOption);

deleteCommand.SetHandler((nodeRef, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var svc = new TreeService(db);
    var node = svc.ResolveNode(nodeRef);
    if (node == null) { Console.WriteLine($"Node not found: {nodeRef}"); return; }

    if (db.DeleteNode(node.Id))
        Console.WriteLine($"Deleted: {node}");
    else
        Console.WriteLine($"Failed to delete: {node}");
}, deleteNodeArg, dbPathOption);

// ── stats ────────────────────────────────────────────────────────────
var statsCommand = new Command("stats", "Show tree statistics");
statsCommand.AddOption(dbPathOption);

statsCommand.SetHandler((dbPath) =>
{
    using var db = OpenDb(dbPath);
    var svc = new TreeService(db);
    svc.PrintStats();
}, dbPathOption);

// ── update ───────────────────────────────────────────────────────────
var updateCommand = new Command("update", "Update a node's name, content, or type");
var updateNodeArg = new Argument<string>("node", "Node to update (ID or name)");
var updateNameOption = new Option<string?>("--name", "New name");
var updateContentOption = new Option<string?>("--content", "New content");
var updateTypeOption = new Option<string?>("--type", "New type: function or component");
updateCommand.AddArgument(updateNodeArg);
updateCommand.AddOption(updateNameOption);
updateCommand.AddOption(updateContentOption);
updateCommand.AddOption(updateTypeOption);
updateCommand.AddOption(dbPathOption);

updateCommand.SetHandler((nodeRef, name, content, type, dbPath) =>
{
    using var db = OpenDb(dbPath);
    var svc = new TreeService(db);
    var node = svc.ResolveNode(nodeRef);
    if (node == null) { Console.WriteLine($"Node not found: {nodeRef}"); return; }

    if (db.UpdateNode(node.Id, name, content, type))
        Console.WriteLine($"Updated: #{node.Id}");
    else
        Console.WriteLine($"No changes made");
}, updateNodeArg, updateNameOption, updateContentOption, updateTypeOption, dbPathOption);

// ── roots ────────────────────────────────────────────────────────────
var rootsCommand = new Command("roots", "List all root nodes (the origins)");
rootsCommand.AddOption(dbPathOption);

rootsCommand.SetHandler((dbPath) =>
{
    using var db = OpenDb(dbPath);
    var roots = db.GetRoots();
    if (roots.Count == 0) { Console.WriteLine("(no roots)"); return; }
    Console.WriteLine("Root nodes (origins):");
    foreach (var r in roots)
        Console.WriteLine($"  {r}");
}, dbPathOption);

// ── leaves ───────────────────────────────────────────────────────────
var leavesCommand = new Command("leaves", "List all leaf nodes (endpoints)");
leavesCommand.AddOption(dbPathOption);

leavesCommand.SetHandler((dbPath) =>
{
    using var db = OpenDb(dbPath);
    var leaves = db.GetLeaves();
    if (leaves.Count == 0) { Console.WriteLine("(no leaves)"); return; }
    Console.WriteLine("Leaf nodes (endpoints):");
    foreach (var l in leaves)
        Console.WriteLine($"  {l}");
}, dbPathOption);

// ── Register all commands ────────────────────────────────────────────
rootCommand.AddCommand(addCommand);
rootCommand.AddCommand(linkCommand);
rootCommand.AddCommand(unlinkCommand);
rootCommand.AddCommand(decomposeCommand);
rootCommand.AddCommand(composeCommand);
rootCommand.AddCommand(treeCommand);
rootCommand.AddCommand(traceCommand);
rootCommand.AddCommand(listCommand);
rootCommand.AddCommand(showCommand);
rootCommand.AddCommand(searchCommand);
rootCommand.AddCommand(deleteCommand);
rootCommand.AddCommand(statsCommand);
rootCommand.AddCommand(updateCommand);
rootCommand.AddCommand(rootsCommand);
rootCommand.AddCommand(leavesCommand);

return await rootCommand.InvokeAsync(args);

// ── Helpers ──────────────────────────────────────────────────────────
Database OpenDb(string dbPath)
{
    var dir = Path.GetDirectoryName(dbPath);
    if (dir != null && !Directory.Exists(dir))
        Directory.CreateDirectory(dir);
    return new Database(dbPath);
}
