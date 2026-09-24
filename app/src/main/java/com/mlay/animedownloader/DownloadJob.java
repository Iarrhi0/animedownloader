package com.mlay.animedownloader;
import android.content.Context;import androidx.annotation.NonNull;import androidx.work.*;import java.util.*;import java.util.concurrent.Semaphore;
public class DownloadJob extends Worker{
 private static final Semaphore SLOTS=new Semaphore(3);
 public DownloadJob(@NonNull Context c,@NonNull WorkerParameters p){super(c,p);}
 @NonNull public Result doWork(){
  String url=getInputData().getString("url"),anime=getInputData().getString("anime"),lang=getInputData().getString("lang"),file=getInputData().getString("file");if(url==null||!url.startsWith("http"))return Result.failure();
  Map<String,String> headers=new HashMap<>();for(String k:getInputData().getKeyValueMap().keySet())if(k.startsWith("h_")){String v=getInputData().getString(k);if(v!=null)headers.put(k.substring(2),v);}
  boolean acquired=false;try{SLOTS.acquire();acquired=true;final boolean[] ok={false};final String[] err={null};new DownloadEngine().download(getApplicationContext(),url,anime==null?"KAZE":anime,lang==null?"SOURCE":lang,file==null?"video.mp4":file,headers,new DownloadEngine.Listener(){public void progress(long d,long t,long b){setProgressAsync(new Data.Builder().putLong("done",d).putLong("total",t).putLong("bps",b).build());}public void state(String s){if("Terminé".equals(s))ok[0]=true;}public void error(String e){err[0]=e;}});return ok[0]?Result.success():Result.failure(new Data.Builder().putString("error",err[0]==null?"Erreur de téléchargement":err[0]).build());}catch(InterruptedException e){Thread.currentThread().interrupt();return Result.retry();}finally{if(acquired)SLOTS.release();}
 }
}
