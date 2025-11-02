# Ad Placement Guide - Adult Video Site

This guide explains all ad placements across the site and recommends which ad types to use for each location, with a focus on mobile traffic.

## Ad Types Available

Based on the ad types you've shown, here are the placements:

1. **Banner Ads** - 728x90 (desktop), 320x50 (mobile)
2. **Sidebar Ads** - 300x250, 300x600 (desktop), full width (mobile)
3. **In-Content Ads** - 728x90 (desktop), 300x250 (tablet), full width (mobile)
4. **Popunder Ads** - Desktop & Mobile versions
5. **Fullpage Interstitial** - Desktop & Mobile versions
6. **Instant Message/Chat Box** - Bottom right corner (mobile-first)
7. **Sticky Banner** - Always visible bottom banner
8. **In-Stream Video Ads** - Plays before/during/after video
9. **In-Video (VAST) Ads** - Overlay in video player
10. **Video Slider** - Slides in and plays automatically
11. **Outstream Video** - Plays when viewable, pauses when out of view
12. **Recommendation Widget** - Native ads that look like content

---

## Ad Placement Strategy by Page

### **BASE TEMPLATE** (`base.html`)
Global ads that appear on all pages.

#### Header Top Banner (`header-top-banner`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Banner, TrafficJunky Banner
- **Mobile**: 320x50 mobile banner
- **Priority**: HIGH - First impression

#### Footer Top Banner (`footer-top-banner`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Banner, PopAds
- **Mobile**: 320x50 mobile banner
- **Priority**: MEDIUM - End of page view

#### Global Popunder Desktop (`global-popunder-desktop`)
- **Type**: Popunder Ad (Desktop Only)
- **Recommended**: ExoClick Popunder, PopAds
- **Trigger**: On page click anywhere
- **Priority**: HIGH - High conversion for adult sites
- **Note**: Place script in `<head>` or before `</body>`

#### Global Popunder Mobile (`global-popunder-mobile`)
- **Type**: Mobile Popunder (Mobile Only)
- **Recommended**: ExoClick Mobile Popunder
- **Priority**: HIGH - Mobile traffic focus
- **Note**: Place script in `<head>` or before `</body>`

#### Global Fullpage Interstitial Desktop (`global-interstitial-desktop`)
- **Type**: Fullpage Interstitial (Desktop Only)
- **Recommended**: ExoClick Fullpage Interstitial
- **Trigger**: On internal link click
- **Priority**: HIGH - Full screen impact
- **Note**: Place script in `<head>` or before `</body>`

#### Global Fullpage Interstitial Mobile (`global-interstitial-mobile`)
- **Type**: Mobile Fullpage Interstitial (Mobile Only)
- **Recommended**: ExoClick Mobile Fullpage Interstitial
- **Priority**: VERY HIGH - Mobile traffic focus
- **Note**: Place script in `<head>` or before `</body>`

#### Global Instant Message (`global-instant-message`)
- **Type**: Instant Message / Chat Box Ad
- **Recommended**: ExoClick Instant Message, TrafficJunky Chat
- **Position**: Fixed bottom right
- **Priority**: VERY HIGH - Perfect for dating/livecam products
- **Mobile Optimized**: YES - 280px on mobile, 320px on desktop

#### Global Sticky Banner (`global-sticky-banner`)
- **Type**: Sticky Banner (Bottom)
- **Recommended**: ExoClick Sticky Banner
- **Position**: Sticky at bottom of screen
- **Size**: 728x90 (desktop), 320x50 (mobile)
- **Priority**: HIGH - Always visible

---

### **HOME PAGE** (`home.html`)

#### Top Banner (`home-top-banner`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Leaderboard Banner, TrafficJunky
- **Priority**: HIGH - Homepage traffic

#### Sidebar Top (`home-sidebar-top`)
- **Type**: Sidebar Ad (300x250)
- **Recommended**: ExoClick Rectangle, PropellerAds
- **Priority**: MEDIUM - Above fold sidebar

#### Sidebar Bottom (`home-sidebar-bottom`)
- **Type**: Sidebar Ad (300x600)
- **Recommended**: ExoClick Wide Skyscraper
- **Priority**: MEDIUM - Below categories

#### In-Content Ad 1 (`home-incontent-1`)
- **Position**: After 4th video
- **Type**: In-Content Banner (728x90)
- **Recommended**: ExoClick Banner, Native Ads
- **Priority**: MEDIUM

#### In-Content Ad 2 (`home-incontent-2`)
- **Position**: After 8th video
- **Type**: In-Content Banner (728x90)
- **Recommended**: ExoClick Banner, Native Ads
- **Priority**: MEDIUM

#### Recommendation Widget (`home-recommendation-1`)
- **Position**: After 12th video
- **Type**: Recommendation Widget (Native Ads)
- **Recommended**: ExoClick Recommendation Widget
- **Priority**: HIGH - Looks like content, high CTR
- **Fully Responsive**: Desktop, mobile, tablet

#### Bottom Banner (`home-bottom-banner`)
- **Type**: Leaderboard Banner (970x250)
- **Recommended**: ExoClick Leaderboard, TrafficJunky
- **Priority**: MEDIUM - Large impact area

---

### **VIDEO DETAIL PAGE** (`video_detail.html`)
**MOST IMPORTANT PAGE** - Users spend most time here. Maximize revenue.

#### Top Banner (`video-top-banner`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Banner, TrafficJunky
- **Priority**: HIGH - Above video

#### In-Stream Video Ad (`video-instream`)
- **Type**: In-Stream Video Ad
- **Recommended**: ExoClick In-Stream, VAST
- **Priority**: VERY HIGH - Plays before/during/after video
- **CPV Based**: High conversion rate
- **Works with**: Video.js player

#### Below Video Player (`video-below-player`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: HIGH - Right after video

#### Sidebar Top (`video-sidebar-top`)
- **Type**: Sidebar Ad (300x250)
- **Recommended**: ExoClick Rectangle
- **Priority**: MEDIUM - Above popular videos

#### Sidebar Bottom (`video-sidebar-bottom`)
- **Type**: Sidebar Ad (300x600)
- **Recommended**: ExoClick Wide Skyscraper
- **Priority**: MEDIUM - Below popular videos

#### Info-Comments Banner (`video-info-comments`)
- **Type**: In-Content Banner (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: MEDIUM - Between content sections

#### Video Slider (`video-slider`)
- **Type**: Video Slider Ad
- **Recommended**: ExoClick Video Slider
- **Position**: Fixed bottom right
- **Priority**: HIGH - Auto-plays, high engagement
- **Customizable**: Frequency capping, close button delay

#### After Related Videos (`video-after-related`)
- **Type**: Leaderboard Banner (970x250)
- **Recommended**: ExoClick Leaderboard
- **Priority**: MEDIUM - After related content

#### Outstream Video (`video-outstream`)
- **Type**: Outstream Video Ad
- **Recommended**: ExoClick Outstream Video
- **Priority**: HIGH - Auto-plays on mute when viewable
- **Mobile Optimized**: YES - Perfect for mobile traffic
- **Behavior**: Pauses when out of view

---

### **VIDEOS LISTING PAGE** (`videos.html`)

#### Top Banner (`videos-top-banner`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: HIGH

#### Sidebar Top (`videos-sidebar-top`)
- **Type**: Sidebar Ad (300x250)
- **Recommended**: ExoClick Rectangle
- **Priority**: MEDIUM

#### Sidebar Bottom (`videos-sidebar-bottom`)
- **Type**: Sidebar Ad (300x600)
- **Recommended**: ExoClick Wide Skyscraper
- **Priority**: MEDIUM

#### In-Content Ad 1 (`videos-incontent-1`)
- **Position**: After 4th video
- **Type**: In-Content Banner (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: MEDIUM

#### In-Content Ad 2 (`videos-incontent-2`)
- **Position**: After 8th video
- **Type**: In-Content Banner (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: MEDIUM

#### Recommendation Widget (`videos-recommendation-1`)
- **Position**: After 12th video
- **Type**: Recommendation Widget
- **Recommended**: ExoClick Recommendation Widget
- **Priority**: HIGH - Native content style

---

### **SEARCH PAGE** (`search.html`)

#### Top Banner (`search-top-banner`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: HIGH

#### In-Content Ad 1 (`search-incontent-1`)
- **Position**: After 4th search result
- **Type**: In-Content Banner (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: MEDIUM

#### In-Content Ad 2 (`search-incontent-2`)
- **Position**: After 8th search result
- **Type**: In-Content Banner (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: MEDIUM

#### Bottom Banner (`search-bottom-banner`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: MEDIUM - Before pagination

---

### **POPULAR PAGE** (`popular.html`)

#### Top Banner (`popular-top-banner`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: HIGH

#### Middle Banner (`popular-middle-banner`)
- **Position**: Between top trending and all popular
- **Type**: Leaderboard Banner (970x250)
- **Recommended**: ExoClick Leaderboard
- **Priority**: HIGH - Strategic placement

#### In-Content Ad 1 (`popular-incontent-1`)
- **Position**: After 4th video
- **Type**: In-Content Banner (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: MEDIUM

#### In-Content Ad 2 (`popular-incontent-2`)
- **Position**: After 8th video
- **Type**: In-Content Banner (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: MEDIUM

---

### **CATEGORIES PAGE** (`categories.html`)

#### Top Banner (`categories-top-banner`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: HIGH

#### Middle Banner (`categories-middle-banner`)
- **Position**: Between categories grid and stats
- **Type**: Leaderboard Banner (970x250)
- **Recommended**: ExoClick Leaderboard
- **Priority**: MEDIUM

#### Bottom Banner (`categories-bottom-banner`)
- **Type**: Banner Ad (728x90)
- **Recommended**: ExoClick Banner
- **Priority**: MEDIUM

---

## Mobile-First Recommendations

Since your traffic is **mainly mobile**, prioritize:

### **Top Priority Mobile Ad Types:**
1. **Mobile Popunder** - High conversion, less intrusive
2. **Mobile Fullpage Interstitial** - Maximum impact
3. **Instant Message Ad** - Perfect for dating/livecam (mobile optimized)
4. **Mobile Banner** (320x50) - Above fold
5. **Outstream Video** - Auto-plays when viewable

### **Ad Networks Recommended for Mobile:**
- **ExoClick** - Excellent mobile support
- **TrafficJunky** - Strong mobile performance
- **PopAds** - Good mobile popunder
- **PropellerAds** - Mobile-friendly formats

---

## Implementation Instructions

### How to Add Ad Scripts:

1. **Find the ad placeholder** in the template files
2. **Replace the placeholder HTML** with your ad script
3. **Example**:
   ```html
   <!-- Before (placeholder) -->
   <div class="ad-placeholder">...</div>
   
   <!-- After (your ad script) -->
   <script async src="https://a.magsrv.com/ad-provider.js"></script>
   <ins class="eas6a97888e2" data-zoneid="YOUR_ZONE_ID"></ins>
   <script>(AdProvider = window.AdProvider || []).push({"serve": {}});</script>
   ```

### For Popunder/Interstitial Ads:
- Place scripts in `<head>` or before `</body>` tag
- These ads are triggered by user actions (clicks, navigation)
- They don't need visible containers

### For Fixed Position Ads (Instant Message, Slider, Sticky):
- Scripts go in the placeholder location
- CSS handles positioning automatically
- Responsive - adjusts for mobile/desktop

---

## Responsive Behavior

All ads are **fully responsive**:

- **Mobile (< 768px)**: Full width banners, mobile-optimized sizes
- **Tablet (769px - 1024px)**: 728x90 banners, 300x250 sidebars
- **Desktop (> 1024px)**: Full size banners (728x90, 970x250), sidebars (300x250, 300x600)

### Mobile-Specific Features:
- Banner ads: 320x50 on mobile (vs 728x90 desktop)
- Sidebar ads: Full width on mobile
- Instant Message: 280px width on mobile (vs 320px desktop)
- Video Slider: 280px width on mobile (vs 320px desktop)

---

## Testing Checklist

Before going live, test:

- [ ] All ad placeholders are visible
- [ ] Ads display correctly on mobile devices
- [ ] Ads display correctly on desktop
- [ ] Popunder/Interstitial triggers work
- [ ] Fixed position ads (Instant Message, Slider) position correctly
- [ ] Sticky banner stays at bottom
- [ ] No layout breaking on any screen size
- [ ] Ads don't overlap content
- [ ] Mobile banner sizes adjust correctly

---

## Revenue Optimization Tips

1. **Video Detail Page**: Highest priority - users spend most time here
   - Use In-Stream, In-Video, Outstream video ads
   - Multiple banner placements
   - Video Slider for engagement

2. **Home Page**: First impression
   - Top banner above fold
   - Recommendation Widget for native look
   - Multiple placements for maximum exposure

3. **Mobile Traffic**: Focus on:
   - Mobile Popunder (high conversion)
   - Mobile Fullpage Interstitial
   - Instant Message (dating/livecam)
   - Mobile-optimized banner sizes

4. **A/B Testing**: Test different ad types in same positions to find best performers

---

## Ad Placement Summary

| Page | Total Ad Placements | Priority Ads |
|------|---------------------|--------------|
| Base Template | 7 (global) | Popunder, Interstitial, Instant Message, Sticky |
| Home Page | 6 | Top Banner, Recommendation Widget, Sidebar |
| Video Detail | 9 | In-Stream, Outstream, Video Slider, Multiple Banners |
| Videos Listing | 6 | Top Banner, Recommendation Widget, Sidebar |
| Search Page | 4 | Top Banner, In-Content Ads |
| Popular Page | 4 | Top Banner, Middle Leaderboard |
| Categories Page | 3 | Top Banner, Middle Leaderboard |

**Total Ad Placements: 39** across all pages

---

## Need Help?

Each ad placeholder has:
- Clear ID for identification
- Instructions on what type of ad to use
- Responsive CSS already implemented
- Mobile/desktop optimization built-in

Simply paste your ad scripts into the placeholders and they'll work responsively on all devices!

