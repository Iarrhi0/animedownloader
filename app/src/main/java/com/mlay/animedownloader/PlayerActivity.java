package com.mlay.animedownloader;
import android.app.Activity;
import android.net.Uri;
import android.os.Bundle;
import androidx.media3.common.MediaItem;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.ui.PlayerView;

public class PlayerActivity extends Activity {
  private ExoPlayer player;
  @Override public void onCreate(Bundle state) {
    super.onCreate(state);
    PlayerView view = new PlayerView(this);
    setContentView(view);
    String url = getIntent().getStringExtra("url");
    if (url == null || url.trim().isEmpty()) { finish(); return; }
    player = new ExoPlayer.Builder(this).build();
    view.setPlayer(player);
    player.setMediaItem(MediaItem.fromUri(Uri.parse(url)));
    player.prepare();
    player.play();
  }
  @Override protected void onStop() {
    super.onStop();
    if (player != null) { player.release(); player = null; }
  }
}
