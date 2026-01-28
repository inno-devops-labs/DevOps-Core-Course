using Microsoft.AspNetCore.Http;
using ModuWeb;
using ModuWeb.ModuleMessenger;

namespace HealthModule
{
    public class Health : ModuleBase
    {
        public Health()
        {
            Map("/", "GET", HealthStatusHandler);
        }

        private async Task HealthStatusHandler(HttpContext context)
        {
            context.Response.StatusCode = 200;
            var res = await ModuleMessenger.SendAndWaitAsync(new("index", "health", new Dictionary<string, object>()));
            await context.Response.WriteAsJsonAsync(new Dictionary<string, object>()
            {
                {"status", "healthy"},
                {"timestamp", DateTime.Now.ToString("yyyy-MM-ddTHH:mm:ss.fff")},
                {"uptime_seconds", (ulong)(DateTime.Now - (DateTime)(res.Data.GetValueOrDefault("StartTime"))).TotalSeconds}
            });
        }
    }
}

