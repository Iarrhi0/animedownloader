package com.mlay.animedownloader;
import android.content.*;import android.os.*;import android.provider.MediaStore;import java.io.*;import java.net.*;import java.util.*;import java.util.concurrent.*;import java.util.concurrent.atomic.*;
public final class DownloadEngine{
 public interface Listener{void progress(long done,long total,long bps);void state(String s);void error(String e);}
 public void download(Context ctx,String url,String anime,String lang,String file,Map<String,String> headers,Listener l){
  try{
   l.state("Connexion");Probe p=probe(url,headers);
   if(p.total>0&&p.ranges)segmented(ctx,url,anime,lang,file,headers,p.total,l);else single(ctx,url,anime,lang,file,headers,l,p.total);
  }catch(Exception e){l.error(msg(e));}
 }
 private Probe probe(String url,Map<String,String> h)throws Exception{
  HttpURLConnection c=open(url,h);c.setRequestProperty("Range","bytes=0-0");int code=c.getResponseCode();String cr=c.getHeaderField("Content-Range");long total=-1;
  if(cr!=null&&cr.contains("/"))try{total=Long.parseLong(cr.substring(cr.lastIndexOf('/')+1));}catch(Exception ignored){}
  if(total<=0)total=c.getContentLengthLong();boolean ranges=code==206&&total>1;c.disconnect();return new Probe(total,ranges);
 }
 private void segmented(Context ctx,String url,String anime,String lang,String file,Map<String,String> headers,long len,Listener l)throws Exception{
  File dir=new File(ctx.getCacheDir(),"kaze_parts");dir.mkdirs();File[] parts=new File[4];ExecutorService pool=Executors.newFixedThreadPool(4);List<Future<?>> fs=new ArrayList<>();AtomicLong done=new AtomicLong();AtomicReference<Throwable> failure=new AtomicReference<>();long started=System.currentTimeMillis();l.state("Téléchargement • 4 connexions");
  for(int i=0;i<4;i++){final int n=i;final long start=len*i/4,end=(i==3?len-1:len*(i+1)/4-1);parts[i]=new File(dir,clean(file)+"."+i+".part");fs.add(pool.submit(()->{try{HttpURLConnection c=open(url,headers);c.setRequestProperty("Range","bytes="+start+"-"+end);if(c.getResponseCode()!=206)throw new IOException("Le serveur refuse le téléchargement multi-connexions");try(InputStream in=c.getInputStream();OutputStream out=new FileOutputStream(parts[n])){copy(in,out,z->{long d=done.addAndGet(z);l.progress(d,len,d*1000/Math.max(1,System.currentTimeMillis()-started));});}c.disconnect();}catch(Throwable e){failure.compareAndSet(null,e);}}));}
  for(Future<?> x:fs)x.get();pool.shutdown();if(failure.get()!=null){for(File x:parts)if(x!=null)x.delete();throw new IOException(msg(failure.get()));}
  long sum=0;for(File x:parts)sum+=x.length();if(sum!=len){for(File x:parts)x.delete();throw new IOException("Téléchargement incomplet");}
  l.state("Assemblage");saveParts(ctx,parts,anime,lang,file);for(File x:parts)x.delete();l.state("Terminé");
 }
 private void single(Context ctx,String url,String anime,String lang,String file,Map<String,String> headers,Listener l,long total)throws Exception{
  l.state("Téléchargement • 1 connexion");HttpURLConnection c=open(url,headers);int code=c.getResponseCode();if(code<200||code>=300)throw new IOException("HTTP "+code);long len=total>0?total:c.getContentLengthLong();File tmp=new File(ctx.getCacheDir(),clean(file)+".part");AtomicLong done=new AtomicLong();long start=System.currentTimeMillis();try(InputStream in=c.getInputStream();OutputStream out=new FileOutputStream(tmp)){copy(in,out,z->{long d=done.addAndGet(z);l.progress(d,len,d*1000/Math.max(1,System.currentTimeMillis()-start));});}c.disconnect();if(len>0&&tmp.length()!=len){tmp.delete();throw new IOException("Téléchargement incomplet");}saveFile(ctx,tmp,anime,lang,file);tmp.delete();l.state("Terminé");
 }
 private HttpURLConnection open(String url,Map<String,String> headers)throws Exception{HttpURLConnection c=(HttpURLConnection)new URL(url).openConnection();c.setInstanceFollowRedirects(true);c.setConnectTimeout(20000);c.setReadTimeout(30000);if(headers!=null)for(Map.Entry<String,String> e:headers.entrySet()){String k=e.getKey();if(k!=null&&e.getValue()!=null&&!k.equalsIgnoreCase("Range")&&!k.equalsIgnoreCase("Host")&&!k.equalsIgnoreCase("Content-Length"))try{c.setRequestProperty(k,e.getValue());}catch(Exception ignored){}}return c;}
 private interface Counter{void add(int n);}private void copy(InputStream in,OutputStream out,Counter c)throws IOException{byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1){out.write(b,0,n);c.add(n);}}
 private void saveParts(Context ctx,File[] ps,String anime,String lang,String file)throws Exception{android.net.Uri u=insert(ctx,anime,lang,file);try(OutputStream out=ctx.getContentResolver().openOutputStream(u)){for(File p:ps)try(InputStream in=new FileInputStream(p)){copy(in,out,n->{});}}finish(ctx,u);}
 private void saveFile(Context ctx,File src,String anime,String lang,String file)throws Exception{android.net.Uri u=insert(ctx,anime,lang,file);try(InputStream in=new FileInputStream(src);OutputStream out=ctx.getContentResolver().openOutputStream(u)){copy(in,out,n->{});}finish(ctx,u);}
 private android.net.Uri insert(Context ctx,String anime,String lang,String file)throws Exception{if(Build.VERSION.SDK_INT<29)throw new IOException("Android 10 ou supérieur requis pour l’enregistrement KAZE");ContentValues v=new ContentValues();v.put(MediaStore.Downloads.DISPLAY_NAME,clean(file));v.put(MediaStore.Downloads.MIME_TYPE,file.toLowerCase(Locale.ROOT).endsWith(".webm")?"video/webm":"video/mp4");v.put(MediaStore.Downloads.RELATIVE_PATH,Environment.DIRECTORY_DOWNLOADS+"/KAZE/"+clean(anime)+"/"+clean(lang));v.put(MediaStore.Downloads.IS_PENDING,1);android.net.Uri u=ctx.getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,v);if(u==null)throw new IOException("Impossible de créer le fichier");return u;}
 private void finish(Context ctx,android.net.Uri u){if(Build.VERSION.SDK_INT>=29){ContentValues v=new ContentValues();v.put(MediaStore.Downloads.IS_PENDING,0);ctx.getContentResolver().update(u,v,null,null);}}
 private String clean(String s){if(s==null||s.isEmpty())return"KAZE";return s.replaceAll("[\\\\/:*?\"<>|]","_");}private String msg(Throwable e){return e.getMessage()==null?e.getClass().getSimpleName():e.getMessage();}
 private static final class Probe{final long total;final boolean ranges;Probe(long t,boolean r){total=t;ranges=r;}}
}
