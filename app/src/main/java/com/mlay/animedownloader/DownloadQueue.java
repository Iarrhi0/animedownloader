package com.mlay.animedownloader;
import android.content.Context;import androidx.work.*;import java.util.concurrent.TimeUnit;
public final class DownloadQueue{
 public static void add(Context c,String url,String anime,String lang,String file){Data d=new Data.Builder().putString("url",url).putString("anime",anime).putString("lang",lang).putString("file",file).build();Constraints k=new Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build();OneTimeWorkRequest w=new OneTimeWorkRequest.Builder(DownloadJob.class).setInputData(d).setConstraints(k).setBackoffCriteria(BackoffPolicy.EXPONENTIAL,15,TimeUnit.SECONDS).addTag("KAZE_DOWNLOAD").build();WorkManager.getInstance(c).enqueue(w);}
}