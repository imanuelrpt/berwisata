import { CloudSun, CloudRain, CloudFog, Cloud, Sun, CloudLightning, Snowflake, Droplets, Wind } from "lucide-react";

const iconByCode = (code, isDay) => {
  if (code === 0) return isDay ? Sun : CloudSun;
  if (code === 1 || code === 2) return CloudSun;
  if (code === 3) return Cloud;
  if (code >= 45 && code <= 48) return CloudFog;
  if (code >= 51 && code <= 67) return CloudRain;
  if (code >= 71 && code <= 77) return Snowflake;
  if (code >= 80 && code <= 82) return CloudRain;
  if (code >= 85 && code <= 86) return Snowflake;
  if (code >= 95) return CloudLightning;
  return Cloud;
};

export default function WeatherWidget({ weather }) {
  if (!weather) return null;
  const Icon = iconByCode(weather.weather_code ?? 0, weather.is_day);
  return (
    <div className="card flex items-center gap-4 p-4">
      <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-sky-100 text-sky-600">
        <Icon className="h-7 w-7" />
      </span>
      <div className="flex-1">
        <p className="flex items-center gap-2 text-2xl font-extrabold text-ink-900">
          {weather.temperature_c}&deg;C
          <span className="text-sm font-semibold text-ink-500">{weather.condition}</span>
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-500">
          <span className="inline-flex items-center gap-1">
            <Droplets className="h-3.5 w-3.5" /> {weather.humidity}%
          </span>
          <span className="inline-flex items-center gap-1">
            <Wind className="h-3.5 w-3.5" /> {weather.wind_speed_kph} km/j
          </span>
          {weather.precipitation_mm > 0 && (
            <span className="text-sky-600">Curah hujan {weather.precipitation_mm} mm</span>
          )}
        </div>
      </div>
    </div>
  );
}
