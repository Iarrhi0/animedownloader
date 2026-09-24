package com.mlay.animedownloader;
import android.webkit.*;import java.util.*;import java.util.concurrent.ConcurrentHashMap;
public final class MediaDetector {
 public interface Listener { void onMedia(String url,String type); }
 private final Set<String> seen=Collections.newSetFromMap(new ConcurrentHashMap<>());
 public WebViewClient client(Listener l){return new WebViewClient(){
  @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){inspect(r.getUrl().toString(),r.getRequestHeaders(),l);return super.shouldInterceptRequest(v,r);}
  @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){inspect(r.getUrl().toString(),r.getRequestHeaders(),l);return false;}
 };}
 private void inspect(String u,Map<String,String> headers,Listener l){if(u==null||!u.startsWith("http")||!seen.add(u))return;String x=u.toLowerCase(Locale.ROOT);String t=x.contains(".m3u8")?"HLS":(x.contains(".mp4")?"MP4":(x.contains(".webm")?"WEBM":null));if(t!=null)l.onMedia(u,t);}
}
