using System.Text.Json;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Godding.Data;

namespace Godding.Services;

public class WebServer
{
    private readonly string _dbPath;

    public WebServer(string dbPath)
    {
        _dbPath = dbPath;
    }

    public void Start(int port = 5111)
    {
        var builder = WebApplication.CreateSlimBuilder();
        var app = builder.Build();

        app.MapGet("/", () => Results.Content(GetHtml(), "text/html"));

        app.MapGet("/api/tree", () =>
        {
            using var db = new Database(_dbPath);
            var nodes = db.GetAllNodes().Select(n => new
            {
                n.Id, n.Name, n.Content, n.Type,
                Children = db.GetChildren(n.Id).Select(c => c.Id).ToList(),
                Parents = db.GetParents(n.Id).Select(p => p.Id).ToList()
            }).ToList();
            return Results.Json(nodes);
        });

        app.MapGet("/api/balance", () =>
        {
            using var db = new Database(_dbPath);
            var allNodes = db.GetAllNodes();
            var roots = db.GetRoots();
            bool isCycle = roots.Count == 0 && allNodes.Count > 0;

            int orphans = 0;
            int givers = 0, receivers = 0, mutual = 0;
            foreach (var node in allNodes)
            {
                bool hasChildren = db.GetChildren(node.Id).Count > 0;
                bool hasParents = db.GetParents(node.Id).Count > 0;
                if (!hasChildren && !hasParents) orphans++;
                if (hasChildren) givers++;
                if (hasParents) receivers++;
                if (hasChildren && hasParents) mutual++;
            }

            return Results.Json(new
            {
                Total = allNodes.Count,
                Orphans = orphans,
                Givers = givers,
                Receivers = receivers,
                Mutual = mutual,
                IsCycle = isCycle,
                Fair = orphans == 0 && allNodes.Count > 0
            });
        });

        app.MapPost("/api/add", async (HttpRequest req) =>
        {
            var body = await JsonSerializer.DeserializeAsync<JsonElement>(req.Body);
            var name = body.GetProperty("name").GetString()!;
            var content = body.TryGetProperty("content", out var c) ? c.GetString() : null;
            var type = body.TryGetProperty("type", out var t) ? t.GetString() ?? "function" : "function";

            using var db = new Database(_dbPath);
            var id = db.AddNode(name, content, type);
            return Results.Json(new { Id = id, Name = name, Type = type });
        });

        app.MapPost("/api/link", async (HttpRequest req) =>
        {
            var body = await JsonSerializer.DeserializeAsync<JsonElement>(req.Body);
            var parentId = body.GetProperty("parentId").GetInt64();
            var childId = body.GetProperty("childId").GetInt64();

            using var db = new Database(_dbPath);
            try
            {
                db.AddEdge(parentId, childId);
                return Results.Json(new { Ok = true });
            }
            catch
            {
                return Results.Json(new { Ok = false, Error = "Link already exists or invalid nodes" });
            }
        });

        app.MapPost("/api/unlink", async (HttpRequest req) =>
        {
            var body = await JsonSerializer.DeserializeAsync<JsonElement>(req.Body);
            var parentId = body.GetProperty("parentId").GetInt64();
            var childId = body.GetProperty("childId").GetInt64();

            using var db = new Database(_dbPath);
            var removed = db.RemoveEdge(parentId, childId);
            return Results.Json(new { Ok = removed });
        });

        app.MapDelete("/api/node/{id}", (long id) =>
        {
            using var db = new Database(_dbPath);
            var removed = db.DeleteNode(id);
            return Results.Json(new { Ok = removed });
        });

        Console.WriteLine($"Godding is running at http://localhost:{port}");
        Console.WriteLine("Open it in your browser. Press Ctrl+C to stop.");

        try
        {
            System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
            {
                FileName = $"http://localhost:{port}",
                UseShellExecute = true
            });
        }
        catch { }

        app.Run($"http://localhost:{port}");
    }

    private string GetHtml() => """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Godding</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, system-ui, sans-serif; background: #0a0a0a; color: #e0e0e0; overflow: hidden; }
canvas { display: block; cursor: grab; }
canvas:active { cursor: grabbing; }

#panel {
    position: fixed; top: 16px; left: 16px; width: 280px;
    background: #1a1a1a; border: 1px solid #333; border-radius: 12px;
    padding: 20px; z-index: 10; font-size: 14px;
}
#panel h1 { font-size: 18px; margin-bottom: 4px; color: #fff; }
#panel .subtitle { color: #888; font-size: 12px; margin-bottom: 16px; font-style: italic; }

.section { margin-bottom: 16px; }
.section label { display: block; color: #aaa; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px; }
input, select {
    width: 100%; padding: 8px 10px; background: #111; border: 1px solid #333;
    border-radius: 6px; color: #e0e0e0; font-size: 13px; outline: none;
}
input:focus, select:focus { border-color: #4a9eff; }
button {
    padding: 8px 14px; background: #222; border: 1px solid #444;
    border-radius: 6px; color: #e0e0e0; cursor: pointer; font-size: 13px; width: 100%;
}
button:hover { background: #333; border-color: #666; }
button.primary { background: #1a3a5c; border-color: #4a9eff; }
button.primary:hover { background: #244a70; }
button.danger { background: #3a1a1a; border-color: #ff4a4a; }
button.danger:hover { background: #4a2222; }

#balance {
    position: fixed; bottom: 16px; left: 16px; width: 280px;
    background: #1a1a1a; border: 1px solid #333; border-radius: 12px;
    padding: 16px; z-index: 10; font-size: 13px;
}
#balance .verdict { font-size: 16px; font-weight: bold; margin-bottom: 8px; }
#balance .verdict.fair { color: #4ade80; }
#balance .verdict.unfair { color: #f87171; }
.stat { display: flex; justify-content: space-between; padding: 3px 0; }
.stat .val { color: #fff; }

#info {
    position: fixed; top: 16px; right: 16px; width: 260px;
    background: #1a1a1a; border: 1px solid #333; border-radius: 12px;
    padding: 16px; z-index: 10; font-size: 13px; display: none;
}
#info h3 { margin-bottom: 8px; color: #fff; }
#info .close { position: absolute; top: 8px; right: 12px; cursor: pointer; color: #888; font-size: 18px; }
#info .close:hover { color: #fff; }

.link-mode { background: #1a3a2a !important; border-color: #4ade80 !important; }
</style>
</head>
<body>
<canvas id="c"></canvas>

<div id="panel">
    <h1>Godding</h1>
    <div class="subtitle">The hand that gives is connected to the hand that receives.</div>

    <div class="section">
        <label>Add a node</label>
        <input id="nodeName" placeholder="Name" style="margin-bottom:6px">
        <input id="nodeContent" placeholder="Description (optional)" style="margin-bottom:6px">
        <select id="nodeType" style="margin-bottom:8px">
            <option value="function">Function (raw)</option>
            <option value="component">Component (compressed)</option>
        </select>
        <button class="primary" onclick="addNode()">Add</button>
    </div>

    <div class="section">
        <label>Connect</label>
        <button id="linkBtn" onclick="toggleLinkMode()">Click two nodes to link them</button>
    </div>

    <div class="section">
        <button onclick="loadTree()">Refresh</button>
    </div>
</div>

<div id="balance">
    <div class="verdict" id="verdict">Loading...</div>
    <div id="balanceStats"></div>
</div>

<div id="info">
    <span class="close" onclick="closeInfo()">&times;</span>
    <h3 id="infoName"></h3>
    <div id="infoDetails"></div>
    <div style="margin-top:12px">
        <button class="danger" id="deleteBtn" onclick="deleteSelected()">Delete</button>
    </div>
</div>

<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
let W, H;
let nodes = [], edges = [];
let dragging = null, dragOff = {x:0,y:0};
let panX = 0, panY = 0, isPanning = false, panStart = {x:0,y:0};
let linkMode = false, linkFrom = null;
let selected = null;
let balanceData = null;

function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
    draw();
}
window.addEventListener('resize', resize);

async function loadTree() {
    const resp = await fetch('/api/tree');
    const data = await resp.json();

    const existingPositions = {};
    nodes.forEach(n => { existingPositions[n.id] = {x: n.x, y: n.y}; });

    nodes = data.map((d, i) => {
        const existing = existingPositions[d.id];
        const angle = (i / data.length) * Math.PI * 2;
        const r = 150 + data.length * 15;
        return {
            id: d.id, name: d.name, content: d.content, type: d.type,
            children: d.children, parents: d.parents,
            x: existing ? existing.x : W/2 + Math.cos(angle) * r + panX,
            y: existing ? existing.y : H/2 + Math.sin(angle) * r + panY,
            vx: 0, vy: 0
        };
    });

    edges = [];
    nodes.forEach(n => {
        n.children.forEach(cid => {
            edges.push({from: n.id, to: cid});
        });
    });

    loadBalance();
    simulate();
}

async function loadBalance() {
    const resp = await fetch('/api/balance');
    balanceData = await resp.json();

    const v = document.getElementById('verdict');
    const s = document.getElementById('balanceStats');

    if (balanceData.fair) {
        v.textContent = 'FAIR FOR ALL';
        v.className = 'verdict fair';
    } else {
        v.textContent = 'NOT YET FAIR';
        v.className = 'verdict unfair';
    }

    const structure = balanceData.isCycle ? 'Cycle' : 'Tree';
    s.innerHTML = `
        <div class="stat"><span>Structure</span><span class="val">${structure}</span></div>
        <div class="stat"><span>Nodes</span><span class="val">${balanceData.total}</span></div>
        <div class="stat"><span>Orphans</span><span class="val">${balanceData.orphans}</span></div>
        <div class="stat"><span>Mutuality</span><span class="val">${balanceData.total > 0 ? Math.round(balanceData.mutual/balanceData.total*100) : 0}%</span></div>
    `;
    draw();
}

function simulate() {
    for (let iter = 0; iter < 100; iter++) {
        // Repulsion between all nodes
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i+1; j < nodes.length; j++) {
                let dx = nodes[j].x - nodes[i].x;
                let dy = nodes[j].y - nodes[i].y;
                let d = Math.sqrt(dx*dx + dy*dy) || 1;
                let f = 8000 / (d * d);
                nodes[i].vx -= dx/d * f;
                nodes[i].vy -= dy/d * f;
                nodes[j].vx += dx/d * f;
                nodes[j].vy += dy/d * f;
            }
        }

        // Attraction along edges
        edges.forEach(e => {
            const a = nodes.find(n => n.id === e.from);
            const b = nodes.find(n => n.id === e.to);
            if (!a || !b) return;
            let dx = b.x - a.x;
            let dy = b.y - a.y;
            let d = Math.sqrt(dx*dx + dy*dy) || 1;
            let f = (d - 120) * 0.05;
            a.vx += dx/d * f;
            a.vy += dy/d * f;
            b.vx -= dx/d * f;
            b.vy -= dy/d * f;
        });

        // Center gravity
        nodes.forEach(n => {
            n.vx += (W/2 - n.x) * 0.001;
            n.vy += (H/2 - n.y) * 0.001;
            n.vx *= 0.85;
            n.vy *= 0.85;
            if (n !== dragging) {
                n.x += n.vx;
                n.y += n.vy;
            }
        });
    }
    draw();
}

function draw() {
    ctx.clearRect(0, 0, W, H);

    // Edges
    edges.forEach(e => {
        const a = nodes.find(n => n.id === e.from);
        const b = nodes.find(n => n.id === e.to);
        if (!a || !b) return;

        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Arrow
        const angle = Math.atan2(b.y - a.y, b.x - a.x);
        const r = 22;
        const ax = b.x - Math.cos(angle) * r;
        const ay = b.y - Math.sin(angle) * r;
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(ax - Math.cos(angle - 0.3) * 10, ay - Math.sin(angle - 0.3) * 10);
        ctx.lineTo(ax - Math.cos(angle + 0.3) * 10, ay - Math.sin(angle + 0.3) * 10);
        ctx.closePath();
        ctx.fillStyle = '#555';
        ctx.fill();
    });

    // Nodes
    nodes.forEach(n => {
        const isOrphan = n.children.length === 0 && n.parents.length === 0;
        const isSelected = selected && selected.id === n.id;
        const isLinkFrom = linkFrom && linkFrom.id === n.id;
        const r = 20;

        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);

        if (isOrphan) ctx.fillStyle = '#3a1a1a';
        else if (n.type === 'component') ctx.fillStyle = '#1a2a3a';
        else ctx.fillStyle = '#1a3a1a';

        ctx.fill();

        ctx.lineWidth = isSelected || isLinkFrom ? 3 : 1.5;
        if (isOrphan) ctx.strokeStyle = '#ff4a4a';
        else if (isLinkFrom) ctx.strokeStyle = '#4ade80';
        else if (isSelected) ctx.strokeStyle = '#4a9eff';
        else ctx.strokeStyle = '#555';
        ctx.stroke();

        // Label
        ctx.fillStyle = '#e0e0e0';
        ctx.font = '12px -apple-system, system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(n.name, n.x, n.y + r + 16);

        // Type indicator
        ctx.fillStyle = '#888';
        ctx.font = '9px monospace';
        ctx.fillText(n.type === 'component' ? 'C' : 'F', n.x, n.y + 4);
    });
}

function getNode(x, y) {
    for (let i = nodes.length - 1; i >= 0; i--) {
        const n = nodes[i];
        const dx = x - n.x, dy = y - n.y;
        if (dx*dx + dy*dy < 20*20) return n;
    }
    return null;
}

canvas.addEventListener('mousedown', e => {
    const node = getNode(e.clientX, e.clientY);
    if (linkMode && node) {
        if (!linkFrom) {
            linkFrom = node;
            draw();
        } else if (node.id !== linkFrom.id) {
            createLink(linkFrom.id, node.id);
            linkFrom = null;
            linkMode = false;
            document.getElementById('linkBtn').classList.remove('link-mode');
            document.getElementById('linkBtn').textContent = 'Click two nodes to link them';
        }
        return;
    }

    if (node) {
        dragging = node;
        dragOff = {x: e.clientX - node.x, y: e.clientY - node.y};
        showInfo(node);
    } else {
        isPanning = true;
        panStart = {x: e.clientX, y: e.clientY};
        closeInfo();
    }
});

canvas.addEventListener('mousemove', e => {
    if (dragging) {
        dragging.x = e.clientX - dragOff.x;
        dragging.y = e.clientY - dragOff.y;
        draw();
    } else if (isPanning) {
        const dx = e.clientX - panStart.x;
        const dy = e.clientY - panStart.y;
        nodes.forEach(n => { n.x += dx; n.y += dy; });
        panStart = {x: e.clientX, y: e.clientY};
        draw();
    }
});

canvas.addEventListener('mouseup', () => {
    dragging = null;
    isPanning = false;
});

function showInfo(node) {
    selected = node;
    document.getElementById('info').style.display = 'block';
    document.getElementById('infoName').textContent = `${node.type === 'component' ? '[C]' : '[F]'} #${node.id} ${node.name}`;
    document.getElementById('infoDetails').innerHTML = `
        ${node.content ? `<p style="color:#aaa;margin-bottom:8px">${node.content}</p>` : ''}
        <div class="stat"><span>Parents</span><span class="val">${node.parents.length}</span></div>
        <div class="stat"><span>Children</span><span class="val">${node.children.length}</span></div>
        <div class="stat"><span>Gives</span><span class="val">${node.children.length > 0 ? 'Yes' : 'No'}</span></div>
        <div class="stat"><span>Receives</span><span class="val">${node.parents.length > 0 ? 'Yes' : 'No'}</span></div>
    `;
    draw();
}

function closeInfo() {
    selected = null;
    document.getElementById('info').style.display = 'none';
    draw();
}

function toggleLinkMode() {
    linkMode = !linkMode;
    linkFrom = null;
    const btn = document.getElementById('linkBtn');
    if (linkMode) {
        btn.classList.add('link-mode');
        btn.textContent = 'Select first node...';
    } else {
        btn.classList.remove('link-mode');
        btn.textContent = 'Click two nodes to link them';
    }
}

async function addNode() {
    const name = document.getElementById('nodeName').value.trim();
    if (!name) return;
    const content = document.getElementById('nodeContent').value.trim() || null;
    const type = document.getElementById('nodeType').value;

    await fetch('/api/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, content, type})
    });

    document.getElementById('nodeName').value = '';
    document.getElementById('nodeContent').value = '';
    loadTree();
}

async function createLink(parentId, childId) {
    await fetch('/api/link', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({parentId, childId})
    });
    loadTree();
}

async function deleteSelected() {
    if (!selected) return;
    await fetch(`/api/node/${selected.id}`, {method: 'DELETE'});
    closeInfo();
    loadTree();
}

document.getElementById('nodeName').addEventListener('keydown', e => {
    if (e.key === 'Enter') addNode();
});

resize();
loadTree();
</script>
</body>
</html>
""";
}
