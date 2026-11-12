"use strict";

const scope = self.registration.scope;
const prefix = `sessia:${scope}:`;
const cacheName = `${prefix}2`;
const paths = [
  "./", "./index.html", "./style.css", "./app.js", "./data.json",
  "./manifest.json", "./icon-180.png", "./icon-192.png", "./icon-512.png",
];
const assets = new Set(paths.map(path => new URL(path, scope).href));
const dataUrl = new URL("./data.json", scope).href;
const figurePath = /^\.\/figures\/[a-z0-9-]+\.(?:png|svg)$/;

self.addEventListener("install", event => {
  event.waitUntil((async () => {
    const cache = await caches.open(cacheName);
    await cache.addAll(paths.map(path => new Request(new URL(path, scope), { cache: "reload" })));
    const data = await (await cache.match(dataUrl)).json();
    const figures = new Set(data.subjects.flatMap(subject => subject.topics)
      .flatMap(topic => topic.blocks)
      .filter(block => block.kind === "figure" && figurePath.test(block.src))
      .map(block => block.src));
    await cache.addAll([...figures].map(path => new Request(new URL(path, scope), { cache: "reload" })));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) {
      if (key.startsWith(prefix) && key !== cacheName) await caches.delete(key);
    }
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", event => {
  const request = event.request;
  if (request.method !== "GET" || !request.url.startsWith(scope)) return;
  const url = new URL(request.url);
  url.search = "";
  const key = request.mode === "navigate" ? scope : url.href;
  if (!assets.has(key) && !figurePath.test("./" + key.slice(scope.length))) return;
  event.respondWith((async () => {
    const cache = await caches.open(cacheName);
    try {
      const response = await fetch(request, { cache: "no-cache" });
      if (response.ok && !response.redirected) {
        await cache.put(key, response.clone());
        return response;
      }
      return (await cache.match(key)) || response;
    } catch {
      return (await cache.match(key)) || Response.error();
    }
  })());
});
