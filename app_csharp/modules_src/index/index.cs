using Microsoft.AspNetCore.Http;
using ModuWeb;
using System.Runtime.InteropServices;
using ModuWeb.Cors;
using ModuWeb.ModuleMessenger;

namespace IndexModule
{
    public class GeneralInfo(HttpContext ctx, DateTime startTime)
    {
        public ServiceInfo service { get; } = new();
        public SystemInfo system { get; } = new();
        public RuntimeInfo runtime { get; } = new(startTime);
        public RequestInfo request { get; } = new(ctx);
        public Dictionary<string, string>[] endpoints { get; } = [
            new Dictionary<string, string>() {{ "path", "/" }, { "method", "GET" }, { "description", "Service information" } },
            new Dictionary<string, string>() {{ "path", "/index" }, { "method", "GET" }, { "description", "Service information" } },
            new Dictionary<string, string>() {{ "path", "/health" }, { "method", "GET" }, { "description", "Health check" } }
        ];
    }
    public class ServiceInfo
    {
        public string name { get; } = "devops-info-service";
        public string version { get; } = "1.0.0";
        public string description { get; } = "DevOps course info service";
        public string framework { get; } = "ASP.NET";
    }
    public class SystemInfo
    {
        public string hostname { get; } = Environment.MachineName;
        public string platform { get; } = GetPlatformName();
        public string platform_version { get; } = GetPlatformVersion();
        public string architecture { get; } = RuntimeInformation.ProcessArchitecture.ToString().ToLower();
        public string cpu_count { get; } = Environment.ProcessorCount.ToString();
        public string aspnet_version { get; } = "9.0.2";
        static string GetPlatformName()
        {
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
                return "Linux";
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
                return "Windows";
            if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
                return "macOS";

            return RuntimeInformation.OSDescription;
        }
        static string GetPlatformVersion()
        {
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
            {
                try
                {
                    if (File.Exists("/etc/os-release"))
                    {
                        var lines = File.ReadAllLines("/etc/os-release");
                        var version = lines.FirstOrDefault(l => l.StartsWith("VERSION_ID="));
                        if (version != null)
                        {
                            return version.Split('=')[1].Trim('"');
                        }
                    }

                    if (File.Exists("/etc/issue"))
                    {
                        var content = File.ReadAllText("/etc/issue");
                        return content.Split('\n')[0].Trim();
                    }
                }
                catch { }
            }
            return Environment.OSVersion.VersionString;
        }
    }
    public class RuntimeInfo(DateTime startTime)
    {
        public ulong uptime_seconds { get; } = (ulong)(DateTime.Now - startTime).TotalSeconds;
        public string uptime_human { get; } = $"{(ulong)(DateTime.Now - startTime).TotalHours}h. {(ulong)(DateTime.Now - startTime).TotalMinutes}m.";
        public string current_time { get; } = DateTime.Now.ToString("yyyy-MM-ddTHH:mm:ss.fff");
        public string timezone { get; } = TimeZoneInfo.Local.Id;
    }
    public class RequestInfo(HttpContext ctx)
    {
        public string client_ip { get; } = ctx.Connection.RemoteIpAddress.ToString();
        public string user_agent { get; } = ctx.Request.Headers[Headers.UserAgent];
        public string method { get; } = "GET";
        public string path { get; } = ctx.Request.Path;

    }
    public class Index : ModuleBase
    {
        public override string ModuleName { get; } = "index";
        static DateTime startTime = DateTime.Now;

        public Index()
        {
            Map("/", "GET", ServiceInfoHandler);
        }

        public override Task OnModuleLoad()
        {
            ModuleMessenger.Subscribe(MessageHandler);
            return Task.CompletedTask;
        }

        private async void MessageHandler(ModuleMessage msg)
        {
            if (msg.From == "health")
            {
                Logger.Info("StartTime request from health module", "Index Module");
                msg.Reply(new(){{"StartTime", startTime}});
            }
        }

        private async Task ServiceInfoHandler(HttpContext context)
        {
            context.Response.StatusCode = 200;
            await context.Response.WriteAsJsonAsync(new GeneralInfo(context, startTime));
        }
    }
}

