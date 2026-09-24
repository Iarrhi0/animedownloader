package com.mlay.animedownloader;
import android.webkit.*;import java.util.*;import java.util.concurrent.ConcurrentHashMap;
public final class MediaDetector {
 public interface Listener { void onMedia(String url,String type,Map<String,String> headers); }
 private final Set<String> seen=Collections.newSetFromMap(new ConcurrentHashMap<>());
 public WebViewClient client(Listener l){return new WebViewClient(){
  @Override public WebResourceResponse shouldInterceptRequest(WebView v,WebResourceRequest r){inspect(r.getUrl().toString(),r.getRequestHeaders(),l);return super.shouldInterceptRequest(v,r);}
  @Override public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){inspect(r.getUrl().toString(),r.getRequestHeaders(),l);return false;}
 };}
 private void inspect(String u,Map<String,String> headers,Listener l){
  if(u==null||!u.startsWith("http"))return;
  String x=u.toLowerCase(Locale.ROOT),accept="";
  if(headers!=null)for(Map.Entry<String,String> e:headers.entrySet())if("accept".equalsIgnoreCase(e.getKey()))accept=e.getValue()==null?"":e.getValue().toLowerCase(Locale.ROOT);
  String t=x.contains(".m3u8")?"HLS":(x.contains(".mp4")?"MP4":(x.contains(".webm")?"WEBM":(accept.contains("video/")?"VIDEO":null)));
  if(t!=null&&seen.add(u))l.onMedia(u,t,headers==null?Collections.emptyMap():new HashMap<>(headers));
 }
}
