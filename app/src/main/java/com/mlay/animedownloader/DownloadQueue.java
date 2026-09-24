package com.mlay.animedownloader;
import android.content.Context;import androidx.work.*;import java.util.*;import java.util.concurrent.TimeUnit;
public final class DownloadQueue{
 public static void add(Context c,String url,String anime,String lang,String file){add(c,url,anime,lang,file,Collections.emptyMap(),"AUTO","720p");}
 public static void add(Context c,String url,String anime,String lang,String file,Map<String,String> headers){add(c,url,anime,lang,file,headers,"AUTO","720p");}
 public static void add(Context c,String url,String anime,String lang,String file,Map<String,String> headers,String type,String quality){
  Data.Builder b=new Data.Builder().putString("url",url).putString("anime",anime).putString("lang",lang).putString("file",file).putString("type",type).putString("quality",quality);
  int i=0;if(headers!=null)for(Map.Entry<String,String> e:headers.entrySet()){if(i++>=20)break;String k=e.getKey(),v=e.getValue();if(k!=null&&v!=null&&v.length()<2000)b.putString("h_"+k,v);}
  Constraints k=new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();
  OneTimeWorkRequest w=new OneTimeWorkRequest.Builder(DownloadJob.class).setInputData(b.build()).setConstraints(k).setBackoffCriteria(BackoffPolicy.EXPONENTIAL,15,TimeUnit.SECONDS).addTag("KAZE_DOWNLOAD").build();
  WorkManager.getInstance(c).enqueue(w);
 }
}
