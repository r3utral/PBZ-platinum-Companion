/* Platinum Companion v1.0.1 — increase CACHE_VERSION when publishing updates. */
const CACHE_VERSION='platinum-companion-app-v1.0.0';
const ASSETS=['./','./index.html','./manifest.webmanifest','./icons/icon-192.png','./icons/icon-512.png'];
self.addEventListener('install', event=>{
  event.waitUntil((async()=>{
    const cache=await caches.open(CACHE_VERSION);
    await cache.addAll(ASSETS);
    await self.skipWaiting();
  })());
});
self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    for(const key of await caches.keys()){
      if(key.startsWith('platinum-companion-app-')&&key!==CACHE_VERSION)await caches.delete(key);
    }
    await self.clients.claim();
  })());
});
self.addEventListener('fetch',event=>{
  const request=event.request;
  if(request.method!=='GET')return;
  const url=new URL(request.url);
  if(url.origin!==self.location.origin||!url.pathname.startsWith(new URL(self.registration.scope).pathname))return;
  if(request.mode==='navigate'){
    event.respondWith((async()=>{
      try{
        const response=await fetch(request);
        if(response.ok){const cache=await caches.open(CACHE_VERSION);await cache.put('./index.html',response.clone())}
        return response;
      }catch(e){return (await caches.match(request))||(await caches.match('./index.html'))||Response.error()}
    })());
    return;
  }
  event.respondWith((async()=>{
    const cached=await caches.match(request);
    if(cached)return cached;
    try{const response=await fetch(request);if(response.ok){const cache=await caches.open(CACHE_VERSION);await cache.put(request,response.clone())}return response}
    catch(e){return Response.error()}
  })());
});
